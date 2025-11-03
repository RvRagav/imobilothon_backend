import paho.mqtt.client as mqtt
import json
import logging
from typing import Optional
from app.core.config import MQTT_BROKER, MQTT_PORT

logger = logging.getLogger(__name__)

# Global MQTT client instance
mqtt_client: Optional[mqtt.Client] = None


def on_connect(client, userdata, flags, rc):
    """Callback for when the client connects to the broker."""
    if rc == 0:
        logger.info(f"MQTT client connected to {MQTT_BROKER}:{MQTT_PORT}")
        print(f"✓ MQTT client connected to {MQTT_BROKER}:{MQTT_PORT}")
    else:
        logger.error(f"MQTT connection failed with code {rc}")
        print(f"✗ MQTT connection failed with code {rc}")


def on_disconnect(client, userdata, rc):
    """Callback for when the client disconnects from the broker."""
    logger.info(f"MQTT client disconnected (rc={rc})")
    print(f"MQTT client disconnected (rc={rc})")


def on_publish(client, userdata, mid):
    """Callback for when a message is published."""
    logger.debug(f"MQTT message published (mid={mid})")
    print(f"✓ MQTT message published successfully (mid={mid})")


def connect_mqtt(client_id: str = "hazard_backend") -> mqtt.Client:
    """
    Connect to MQTT broker.
    
    Args:
        client_id: Unique identifier for this MQTT client
        
    Returns:
        Connected MQTT client instance
    """
    global mqtt_client
    
    try:
        client = mqtt.Client(client_id=client_id)
        client.on_connect = on_connect
        client.on_disconnect = on_disconnect
        client.on_publish = on_publish
        
        # Connect to broker
        logger.info(f"Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
        print(f"Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}...")
        
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
        client.loop_start()  # Start network loop in background thread
        
        mqtt_client = client
        return client
        
    except Exception as e:
        logger.error(f"Failed to connect to MQTT broker: {str(e)}")
        print(f"✗ Failed to connect to MQTT broker: {str(e)}")
        raise


def disconnect_mqtt():
    """Disconnect from MQTT broker."""
    global mqtt_client
    
    if mqtt_client:
        try:
            mqtt_client.loop_stop()
            mqtt_client.disconnect()
            logger.info("MQTT client disconnected")
            print("MQTT client disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting MQTT client: {str(e)}")
            print(f"Error disconnecting MQTT client: {str(e)}")
        finally:
            mqtt_client = None


def publish_hazard_alert(
    hazard_id: int,
    hazard_type: str,
    latitude: float,
    longitude: float,
    timestamp: str,
    qos: int = 1
) -> bool:
    """
    Publish hazard alert to MQTT broker.
    
    Args:
        hazard_id: ID of the hazard
        hazard_type: Type of hazard (e.g., "pothole", "debris", "collision")
        latitude: Latitude of the hazard
        longitude: Longitude of the hazard
        timestamp: ISO format timestamp string
        qos: Quality of Service level (0, 1, or 2)
        
    Returns:
        True if message was queued for publishing, False otherwise
    """
    global mqtt_client
    
    if not mqtt_client:
        logger.warning("MQTT client not connected, cannot publish hazard alert")
        print("⚠ MQTT client not connected, cannot publish hazard alert")
        return False
    
    if not mqtt_client.is_connected():
        logger.warning("MQTT client not connected, cannot publish hazard alert")
        print("⚠ MQTT client not connected, cannot publish hazard alert")
        return False
    
    try:
        # Construct topic: hazards/alerts/<hazard_type>
        topic = f"hazards/alerts/{hazard_type}"
        
        # Construct payload
        payload = {
            "hazard_id": hazard_id,
            "hazard_type": hazard_type,
            "latitude": latitude,
            "longitude": longitude,
            "timestamp": timestamp
        }
        
        # Convert to JSON string
        payload_json = json.dumps(payload)
        
        # Publish message
        result = mqtt_client.publish(topic, payload_json, qos=qos)
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            logger.info(
                f"Published hazard alert to {topic}: "
                f"hazard_id={hazard_id}, type={hazard_type}, "
                f"lat={latitude}, lon={longitude}"
            )
            print(
                f"✓ Published hazard alert to {topic}: "
                f"hazard_id={hazard_id}, type={hazard_type}"
            )
            return True
        else:
            logger.error(f"Failed to publish MQTT message, error code: {result.rc}")
            print(f"✗ Failed to publish MQTT message, error code: {result.rc}")
            return False
            
    except Exception as e:
        logger.error(f"Error publishing MQTT message: {str(e)}")
        print(f"✗ Error publishing MQTT message: {str(e)}")
        return False


def is_connected() -> bool:
    """Check if MQTT client is connected."""
    global mqtt_client
    return mqtt_client is not None and mqtt_client.is_connected()

