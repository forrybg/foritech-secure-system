# 📦 Инсталация и конфигурация на Fori Tech Secure System

Това ръководство описва стъпките за инсталиране, конфигуриране и стартиране на системата за защита, архивиране и управление на информация.

---

## 🧱 Предварителни изисквания

- Ubuntu Server 22.04 (или съвместима Linux дистрибуция)
- Docker и Docker Compose
- SSH достъп и root права
- VR или физически сървър с поне 4 CPU, 8 GB RAM, 100 GB SSD

---

## 🔧 Инсталация на зависимости

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install docker.io docker-compose git ufw -y
sudo systemctl enable docker
