"""
Proxmox API Service
Wrapper around proxmoxer library for cluster management
"""
from proxmoxer import ProxmoxAPI
from typing import Dict, List, Optional, Tuple
import logging
from cryptography.fernet import Fernet

from app.config import settings

logger = logging.getLogger(__name__)


class ProxmoxService:
    """Service for interacting with Proxmox API"""
    
    def __init__(self, host: str = None, user: str = None, token_name: str = None, 
                 token_value: str = None, verify_ssl: bool = False):
        """
        Initialize Proxmox API connection
        
        Args:
            host: Proxmox host address
            user: Username  (e.g., 'root@pam')
            token_name: API token name
            token_value: API token value (UUID)
            verify_ssl: Whether to verify SSL certificates
        """
        self.host = host or settings.PROXMOX_HOST
        self.user = user or settings.PROXMOX_USER
        self.token_name = token_name or settings.PROXMOX_TOKEN_NAME
        self.token_value = token_value or settings.PROXMOX_TOKEN_VALUE
        self.verify_ssl = verify_ssl or settings.PROXMOX_VERIFY_SSL
        
        self._proxmox = None
    
    def _get_connection(self) -> ProxmoxAPI:
        """Get or create Proxmox API connection"""
        if self._proxmox is None:
            try:
                self._proxmox = ProxmoxAPI(
                    self.host,
                    user=self.user,
                    token_name=self.token_name,
                    token_value=self.token_value,
                    verify_ssl=self.verify_ssl
                )
                logger.info(f"Connected to Proxmox at {self.host}")
            except Exception as e:
                logger.error(f"Failed to connect to Proxmox: {str(e)}")
                raise
        
        return self._proxmox
    
    def get_cluster_nodes(self) -> List[Dict]:
        """
        Get list of cluster nodes
        
        Returns:
            List of node dictionaries
        """
        try:
            proxmox = self._get_connection()
            nodes = proxmox.nodes.get()
            logger.debug(f"Retrieved {len(nodes)} cluster nodes")
            return nodes
        except Exception as e:
            logger.error(f"Error getting cluster nodes: {str(e)}")
            raise
    
    def get_cluster_resources(self, resource_type: str = None) -> List[Dict]:
        """
        Get cluster resources (VMs, containers, etc.)
        
        Args:
            resource_type: Filter by type ('vm', 'lxc', 'node', 'storage')
            
        Returns:
            List of resource dictionaries
        """
        try:
            proxmox = self._get_connection()
            params = {}
            if resource_type:
                params['type'] = resource_type
            
            resources = proxmox.cluster.resources.get(**params)
            logger.debug(f"Retrieved {len(resources)} cluster resources")
            return resources
        except Exception as e:
            logger.error(f"Error getting cluster resources: {str(e)}")
            raise
    
    def get_all_vms(self) -> List[Dict]:
        """
        Get all VMs and containers from cluster
        
        Returns:
            List of VM/container dictionaries with unified format
        """
        try:
            resources = self.get_cluster_resources()
            
            vms = []
            for resource in resources:
                # Filter for VMs and containers
                if resource.get('type') in ['qemu', 'lxc']:
                    vm_data = {
                        'vmid': resource.get('vmid'),
                        'name': resource.get('name'),
                        'type': resource.get('type'),
                        'node': resource.get('node'),
                        'status': resource.get('status'),
                        'maxmem': resource.get('maxmem'),
                        'maxdisk': resource.get('maxdisk'),
                        'uptime': resource.get('uptime'),
                    }
                    vms.append(vm_data)
            
            logger.info(f"Retrieved {len(vms)} VMs/containers from cluster")
            return vms
        except Exception as e:
            logger.error(f"Error getting all VMs: {str(e)}")
            raise
    
    def get_vm_status(self, node: str, vmid: int, vm_type: str) -> Dict:
        """
        Get current status of a VM or container
        
        Args:
            node: Node name where VM is located
            vmid: VM ID
            vm_type: 'qemu' or 'lxc'
            
        Returns:
            VM status dictionary
        """
        try:
            proxmox = self._get_connection()
            
            if vm_type == 'qemu':
                status = proxmox.nodes(node).qemu(vmid).status.current.get()
            elif vm_type == 'lxc':
                status = proxmox.nodes(node).lxc(vmid).status.current.get()
            else:
                raise ValueError(f"Invalid vm_type: {vm_type}")
            
            logger.debug(f"Got status for {vm_type}/{vmid}: {status.get('status')}")
            return status
        except Exception as e:
            logger.error(f"Error getting VM status: {str(e)}")
            raise
    
    def start_vm(self, node: str, vmid: int, vm_type: str) -> str:
        """
        Start a VM or container
        
        Args:
            node: Node name
            vmid: VM ID
            vm_type: 'qemu' or 'lxc'
            
        Returns:
            Task UPID
        """
        try:
            proxmox = self._get_connection()
            
            if vm_type == 'qemu':
                result = proxmox.nodes(node).qemu(vmid).status.start.post()
            elif vm_type == 'lxc':
                result = proxmox.nodes(node).lxc(vmid).status.start.post()
            else:
                raise ValueError(f"Invalid vm_type: {vm_type}")
            
            logger.info(f"Started {vm_type}/{vmid} on {node}, UPID: {result}")
            return result
        except Exception as e:
            logger.error(f"Error starting VM: {str(e)}")
            raise
    
    def stop_vm(self, node: str, vmid: int, vm_type: str) -> str:
        """
        Stop a VM or container (forced)
        
        Args:
            node: Node name
            vmid: VM ID
            vm_type: 'qemu' or 'lxc'
            
        Returns:
            Task UPID
        """
        try:
            proxmox = self._get_connection()
            
            if vm_type == 'qemu':
                result = proxmox.nodes(node).qemu(vmid).status.stop.post()
            elif vm_type == 'lxc':
                result = proxmox.nodes(node).lxc(vmid).status.stop.post()
            else:
                raise ValueError(f"Invalid vm_type: {vm_type}")
            
            logger.info(f"Stopped {vm_type}/{vmid} on {node}, UPID: {result}")
            return result
        except Exception as e:
            logger.error(f"Error stopping VM: {str(e)}")
            raise
    
    def shutdown_vm(self, node: str, vmid: int, vm_type: str) -> str:
        """
        Gracefully shutdown a VM or container
        
        Args:
            node: Node name
            vmid: VM ID
            vm_type: 'qemu' or 'lxc'
            
        Returns:
            Task UPID
        """
        try:
            proxmox = self._get_connection()
            
            if vm_type == 'qemu':
                result = proxmox.nodes(node).qemu(vmid).status.shutdown.post()
            elif vm_type == 'lxc':
                result = proxmox.nodes(node).lxc(vmid).status.shutdown.post()
            else:
                raise ValueError(f"Invalid vm_type: {vm_type}")
            
            logger.info(f"Shutdown {vm_type}/{vmid} on {node}, UPID: {result}")
            return result
        except Exception as e:
            logger.error(f"Error shutting down VM: {str(e)}")
            raise
    
    def reboot_vm(self, node: str, vmid: int, vm_type: str) -> str:
        """
        Reboot a VM or container
        
        Args:
            node: Node name
            vmid: VM ID
            vm_type: 'qemu' or 'lxc'
            
        Returns:
            Task UPID
        """
        try:
            proxmox = self._get_connection()
            
            if vm_type == 'qemu':
                result = proxmox.nodes(node).qemu(vmid).status.reboot.post()
            elif vm_type == 'lxc':
                result = proxmox.nodes(node).lxc(vmid).status.reboot.post()
            else:
                raise ValueError(f"Invalid vm_type: {vm_type}")
            
            logger.info(f"Rebooted {vm_type}/{vmid} on {node}, UPID: {result}")
            return result
        except Exception as e:
            logger.error(f"Error rebooting VM: {str(e)}")
            raise
    
    def reset_vm(self, node: str, vmid: int, vm_type: str) -> str:
        """
        Reset (hard reboot) a VM
        Note: Only available for qemu VMs
        
        Args:
            node: Node name
            vmid: VM ID
            vm_type: 'qemu'
            
        Returns:
            Task UPID
        """
        try:
            if vm_type != 'qemu':
                raise ValueError("Reset is only available for qemu VMs")
            
            proxmox = self._get_connection()
            result = proxmox.nodes(node).qemu(vmid).status.reset.post()
            
            logger.info(f"Reset {vm_type}/{vmid} on {node}, UPID: {result}")
            return result
        except Exception as e:
            logger.error(f"Error resetting VM: {str(e)}")
            raise
    
    def get_task_status(self, node: str, upid: str) -> Dict:
        """
        Get status of a Proxmox task
        
        Args:
            node: Node name where task is running
            upid: Task UPID
            
        Returns:
            Task status dictionary
        """
        try:
            proxmox = self._get_connection()
            status = proxmox.nodes(node).tasks(upid).status.get()
            return status
        except Exception as e:
            logger.error(f"Error getting task status: {str(e)}")
            raise
    
    def wait_for_task(self, node: str, upid: str, timeout: int = 300) -> Tuple[bool, str]:
        """
        Wait for a task to complete
        
        Args:
            node: Node name
            upid: Task UPID
            timeout: Maximum wait time in seconds
            
        Returns:
            Tuple of (success, status_message)
        """
        import time
        
        start_time = time.time()
        while True:
            if time.time() - start_time > timeout:
                return False, "Task timeout"
            
            try:
                status = self.get_task_status(node, upid)
                
                if status.get('status') == 'stopped':
                    exitstatus = status.get('exitstatus')
                    if exitstatus == 'OK':
                        return True, "Task completed successfully"
                    else:
                        return False, f"Task failed: {exitstatus}"
                
                time.sleep(2)  # Poll every 2 seconds
            except Exception as e:
                return False, f"Error checking task: {str(e)}"


# Singleton instance
_proxmox_service = None


def get_proxmox_service() -> ProxmoxService:
    """Get singleton Proxmox service instance"""
    global _proxmox_service
    if _proxmox_service is None:
        _proxmox_service = ProxmoxService()
    return _proxmox_service
