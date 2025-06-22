# TrueNAS Scale Storage and Networking Patterns

> Research findings from TrueNAS Scale Electric Eel system analysis

## 🗄️ Storage Architecture

### TrueNAS Scale App Storage Structure

```
/mnt/.ix-apps/
├── app_configs/           # App configuration and metadata
│   └── {app_name}/
│       ├── metadata.yaml  # App metadata (versions, capabilities)
│       └── versions/      # Version-specific configs
│           └── {version}/
│               ├── user_config.yaml  # User configuration
│               └── app.yaml          # App deployment spec
├── app_mounts/           # Persistent app data storage
│   └── {app_name}/
│       └── {volume_name}/  # App-specific volumes
└── docker/
    ├── containers/       # Container runtime data
    ├── volumes/         # Docker named volumes
    └── overlay2/        # Container layers
```

### Storage Types in TrueNAS Scale

#### 1. **IX Volumes** (Recommended for Apps)
- **Location**: `/mnt/.ix-apps/app_mounts/{app_name}/{volume_name}/`
- **Purpose**: Persistent application data
- **Characteristics**: 
  - Managed by TrueNAS
  - Survives app updates/restarts
  - ZFS dataset-backed
  - Proper permissions and ACLs

**Example Configuration:**
```yaml
storage:
  data:
    ix_volume_config:
      acl_enable: false
      dataset_name: data
    type: ix_volume
```

#### 2. **Host Path Bind Mounts**
- **Usage**: Direct access to host filesystem
- **Common Patterns**:
  - Media libraries: `/mnt/pool/media:/data/media`
  - Configuration: `/mnt/pool/configs:/config`
  - Logs: `/mnt/pool/logs:/logs`

#### 3. **Docker Named Volumes**
- **Location**: `/mnt/.ix-apps/docker/volumes/`
- **Pattern**: `{app_name}_{service}_{volume_name}`
- **Less common**: TrueNAS prefers IX volumes

### Recommended Storage Patterns

#### ✅ **Best Practices**
```yaml
services:
  webapp:
    image: nginx:latest
    volumes:
      # App data - use IX volume (TrueNAS manages this)
      - app_data:/var/lib/app
      
      # Configuration - bind mount to pool
      - /mnt/pool/configs/nginx:/etc/nginx/conf.d:ro
      
      # Logs - bind mount to pool  
      - /mnt/pool/logs/nginx:/var/log/nginx
      
      # Media/content - bind mount to pool
      - /mnt/pool/media:/usr/share/nginx/html:ro

volumes:
  app_data:  # TrueNAS will create IX volume
```

#### ❌ **Avoid These Patterns**
```yaml
# DON'T: Bind mount to system directories
- /etc/nginx:/etc/nginx

# DON'T: Bind mount to Docker internals  
- /var/lib/docker:/data

# DON'T: Write to read-only system locations
- /usr/share/app:/usr/share/app
```

## 🌐 Networking Architecture

### Network Types Available

#### 1. **Bridge Networks** (Default)
- **Pattern**: `ix-{app_name}_default`
- **Subnet**: `172.16.x.0/24` (auto-assigned)
- **Access**: Via port forwarding to host IP
- **Use Case**: Standard web services

**Example Access:**
- Container: `172.16.2.2:9000`
- Host Access: `nas-ip:31015` → `container:9000`

#### 2. **Macvlan Networks** (Advanced)
- **Network**: Custom macvlan (e.g., `macvlan_network`)
- **Subnet**: Same as LAN (e.g., `10.121.124.0/24`)
- **Access**: Direct IP address on LAN
- **Use Case**: Services needing dedicated IP

**Example Configuration:**
```yaml
networks:
  macvlan_network:
    external: true

services:
  webapp:
    networks:
      macvlan_network:
        ipv4_address: 10.121.124.50  # Dedicated IP
    ports:
      - "80:80"  # Direct access via dedicated IP
```

#### 3. **Host Networking**
- **Access**: Direct host network stack
- **Ports**: Bind directly to host ports
- **Use Case**: Performance-critical or network-discovery services

### Networking Decision Matrix

| Use Case | Network Type | Access Pattern | Example |
|----------|-------------|----------------|---------|
| **Web UI** | Bridge | `nas-ip:port` | Portainer: `nas-ip:31015` |
| **Media Server** | Bridge | `nas-ip:port` | Plex: `nas-ip:32400` |
| **Network Service** | Macvlan | `dedicated-ip:port` | DNS: `10.121.124.50:53` |
| **System Integration** | Host | `nas-ip:port` | Monitoring: `nas-ip:9090` |

### Port Management

#### TrueNAS Port Allocation
- **System Ports**: `1-1024` (reserved)
- **App Ports**: `30000-65535` (auto-assigned)
- **Custom Ports**: Manual assignment possible

#### Port Configuration Examples
```yaml
# Bridge Network (Port Forwarding)
services:
  webapp:
    image: nginx:latest
    ports:
      - "8080:80"    # Will become nas-ip:31xxx → container:80
    networks:
      - default

# Macvlan Network (Direct Access)  
services:
  webapp:
    image: nginx:latest
    ports:
      - "80:80"      # Direct access via dedicated IP:80
    networks:
      macvlan_network:
        ipv4_address: 10.121.124.50
```

## 📋 Conversion Patterns for Scale API Compose Pilot

### Storage Conversion Rules

```python
def convert_storage_patterns(service_config, app_name):
    """Convert Docker Compose volumes to TrueNAS patterns."""
    
    volumes = []
    ix_volumes = {}
    
    for volume in service_config.get('volumes', []):
        if ':' in volume:
            host_path, container_path = volume.split(':', 1)
            
            # Pattern 1: Named volume → IX Volume
            if not host_path.startswith('/'):
                ix_volumes[host_path] = {
                    "type": "ix_volume",
                    "mount_path": container_path
                }
            
            # Pattern 2: Pool mount → Bind mount
            elif host_path.startswith('/mnt/'):
                volumes.append({
                    "type": "host_path", 
                    "host_path": host_path,
                    "mount_path": container_path
                })
            
            # Pattern 3: System path → Warning
            else:
                print(f"⚠️  System path bind mount: {host_path}")
                
    return volumes, ix_volumes
```

### Network Conversion Rules

```python
def convert_network_patterns(compose_data, app_name):
    """Convert Docker Compose networks to TrueNAS patterns."""
    
    services = compose_data.get('services', {})
    networks = compose_data.get('networks', {})
    
    # Check for external macvlan
    if 'macvlan_network' in networks:
        return {
            "type": "macvlan",
            "network_name": "macvlan_network",
            "enable_static_ip": True
        }
    
    # Default to bridge
    return {
        "type": "bridge", 
        "port_forwards": extract_port_forwards(services)
    }
```

### Complete Example Conversion

#### Input Docker Compose:
```yaml
services:
  webapp:
    image: nginx:latest
    ports:
      - "8080:80"
    environment:
      - ENV=prod
    volumes:
      - app_data:/var/lib/app          # → IX Volume
      - /mnt/pool/web:/var/www:ro      # → Host bind mount
      - /mnt/pool/logs:/var/log/nginx  # → Host bind mount
    restart: unless-stopped

volumes:
  app_data:  # Named volume
```

#### Output TrueNAS Config:
```yaml
name: webapp
image:
  repository: nginx
  tag: latest
  
network:
  type: bridge
  port_forwards:
    - host_port: 8080
      container_port: 80
      
storage:
  app_data:
    type: ix_volume
    mount_path: /var/lib/app
  web_content:
    type: host_path
    host_path: /mnt/pool/web
    mount_path: /var/www
    read_only: true
  logs:
    type: host_path  
    host_path: /mnt/pool/logs
    mount_path: /var/log/nginx

environment:
  ENV: prod
  
restart_policy: unless-stopped
```

## 🎯 Recommendations for Scale API Compose Pilot

### 1. **Storage Validation**
- ✅ Allow `/mnt/` bind mounts (pool storage)
- ✅ Convert named volumes to IX volumes
- ⚠️ Warn on system directory mounts
- ❌ Block dangerous system mounts

### 2. **Network Detection**
- 🔍 Auto-detect macvlan network references
- 🔧 Convert to appropriate network type
- 📝 Provide networking guidance

### 3. **Port Management**
- 🎰 Let TrueNAS auto-assign ports for bridge networks
- 🎯 Allow manual port specification for macvlan
- 📊 Report final access URLs

### 4. **User Guidance**
```python
def provide_storage_guidance():
    return {
        "recommended_patterns": [
            "Use /mnt/pool/* for media and configs",
            "Let TrueNAS manage app data with IX volumes", 
            "Separate logs and configs from app data"
        ],
        "networking_advice": [
            "Bridge: Best for web UIs (auto port assignment)",
            "Macvlan: For services needing dedicated IPs",
            "Consider TrueNAS firewall rules for external access"
        ]
    }
```

This research provides the foundation for making Scale API Compose Pilot much more TrueNAS-aware and helpful! 🎯