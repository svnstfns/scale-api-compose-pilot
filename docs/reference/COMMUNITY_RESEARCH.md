# Community Research: TrueNAS Scale Docker Deployment Pain Points

## Key Issues from Forums/Reddit/GitHub:

### 1. **Docker Socket Removal (Cobia 23.10)**
- Docker.sock removed, breaking existing workflows
- Switched to containerd backend
- Many tools rely on docker socket access

### 2. **Complex Custom App Deployment**
- "Installing custom applications via YAML requires advanced knowledge"
- No GUI for docker-compose files
- Shell access to containers problematic

### 3. **Migration Confusion (K3s → Docker in 24.10)**
- Major architectural change
- Old Kubernetes apps incompatible
- Documentation outdated/confusing

### 4. **Storage & Networking Complexity**
- Bind mount permissions issues
- Network configuration unclear
- IX volumes vs host paths confusion

### 5. **Multi-Container Apps**
- No native support for docker-compose stacks
- Each container needs separate app
- Inter-container networking difficult

## Most Requested Features:

1. **Direct Docker Compose Support**
   - "Wish I could just upload my docker-compose.yml"
   - Import existing compose files
   - Multi-container stack support

2. **GUI for Custom Apps**
   - Visual compose builder
   - Easy port/volume mapping
   - No YAML editing required

3. **Migration Tools**
   - Convert K3s apps to Docker
   - Import from Portainer/other systems
   - Backup/restore compose configs

4. **Better Networking**
   - Easy macvlan setup
   - Container-to-container communication
   - Reverse proxy integration

5. **Template Library**
   - Community compose templates
   - One-click deployments
   - Share configurations