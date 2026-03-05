import socket
import logging
from zeroconf import Zeroconf, ServiceInfo, ServiceBrowser, ServiceListener

logger = logging.getLogger(__name__)

class DeviceDiscovery(ServiceListener):
    def __init__(self, device_name, port, on_device_found, on_device_lost=None):
        self.device_name = device_name
        self.port = port
        self.on_device_found = on_device_found
        self.on_device_lost = on_device_lost
        self.zeroconf = Zeroconf()
        self.service_type = "_myapp._tcp.local."

    def start(self):
        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)

            info = ServiceInfo(
                self.service_type,
                f"{self.device_name}.{self.service_type}",
                addresses=[socket.inet_aton(ip)],
                port=self.port,
                properties={"type": "pc", "version": "0.1.0"},
            )

            self.zeroconf.register_service(info)
            logger.info(f"Registered service: {self.device_name} at {ip}:{self.port}")

            ServiceBrowser(self.zeroconf, self.service_type, listener=self)
        except Exception as e:
            logger.error(f"Failed to start discovery: {e}")

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        if info:
            addresses = [socket.inet_ntoa(addr) for addr in info.addresses]
            if addresses:
                ip = addresses[0]
                device_name = name.replace(f".{self.service_type}", "")
                if device_name != self.device_name: # Don't discover ourselves
                    self.on_device_found(device_name, ip, info.port)

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        device_name = name.replace(f".{self.service_type}", "")
        if self.on_device_lost:
            self.on_device_lost(device_name)

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        pass

    def stop(self):
        self.zeroconf.unregister_all_services()
        self.zeroconf.close()