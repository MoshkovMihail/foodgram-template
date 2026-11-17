import os
import time
import logging
import requests
from kubernetes import client, config, watch

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

NTFY_URL = os.getenv("NTFY_URL", "https://ntfy.sh")
NTFY_TOPIC = os.getenv("NTFY_TOPIC")
NAMESPACE = os.getenv("POD_NAMESPACE")

config.load_incluster_config()
v1 = client.CoreV1Api()

IGNORE_REASONS = ("ContainerCreating", "PodInitializing")

def send_alert(pod_name, reason):
    text = f"Pod {pod_name} failed. Reason: {reason}"
    logger.warning(text)
    try:
        requests.post(
            f"{NTFY_URL}/{NTFY_TOPIC}", 
            data=text.encode("utf-8"), 
            headers={"Title": "K8s Alert"}, 
            timeout=5
        )
    except Exception as e:
        logger.error(f"Failed to send alert: {e}")

def main():
    logger.info(f"Watching pods in namespace {NAMESPACE}")
    alerted = set()

    while True:
        try:
            w = watch.Watch()
            for event in w.stream(v1.list_namespaced_pod, namespace=NAMESPACE):
                pod = event["object"]
                name = pod.metadata.name

                if event["type"] == "DELETED":
                    alerted.discard(name)
                    continue

                if name in alerted or pod.metadata.deletion_timestamp:
                    continue

                statuses = (pod.status.init_container_statuses or []) + (pod.status.container_statuses or [])
                for status in statuses:
                    if status.state.waiting and status.state.waiting.reason not in IGNORE_REASONS:
                        alerted.add(name)
                        send_alert(name, status.state.waiting.reason)
                        break
                    elif status.state.terminated and status.state.terminated.exit_code != 0:
                        alerted.add(name)
                        send_alert(name, status.state.terminated.reason)
                        break
        except Exception as e:
            logger.error(f"Watch error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()