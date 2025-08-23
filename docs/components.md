# 🧩 Компоненти на Fori Tech Secure System

Този документ описва основните подсистеми, включени в архитектурата на проекта.

---

## 🔐 1. Firewall (UFW / iptables)

- **Функция**: Филтрира входящ и изходящ трафик
- **Конфигурация**:
```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 443
sudo ufw enable

🛡️ 2. IPS (Suricata)
• 	Функция: Открива и блокира мрежови атаки
• 	Интеграция: Събира логове за SIEM
• 	Конфигурация:  + правила от Emerging Threats

🧠 3. EDR (Wazuh)
• 	Функция: Защита на сървъри и работни станции
• 	Компоненти: Wazuh Manager + Agents
• 	Интеграция: SIEM + Dashboard

🌐 4. VPN (WireGuard)
• 	Функция: Сигурен отдалечен достъп
• 	Конфигурация:  + публични/частни ключове
• 	Портове: UDP 51820

🔑 5. Keycloak (IAM)
• 	Функция: Централизирано управление на достъпа
• 	Функции: MFA, роли, групи, OAuth2
• 	Интеграция: Vault, MinIO, Web UI

🔐 6. Vault (HashiCorp)
• 	Функция: Управление на тайни и криптиране
• 	Модул: Transit Engine за криптиране на архиви
• 	Интеграция: MinIO, Backup скриптове

📦 7. MinIO (S3 хранилище)
• 	Функция: Съхранение на архиви
• 	ACL: Интеграция с Keycloak
• 	Конфигурация:  + 

📊 8. SIEM (Wazuh + Elasticsearch + Kibana)
• 	Функция: Централизирано събиране и анализ на логове
• 	Източници: Suricata, Vault, MinIO, EDR
• 	Dashboard: Grafana или Kibana

🧾 9. NFT лицензиране
• 	Функция: Удостоверяване на достъп чрез Web3
• 	Технологии: ERC-721, IPFS, Smart Contract
• 	Интеграция: Keycloak + Web UI

🖥️ 10. Хардуерни компоненти
• 	VR сървър: Основна платформа
• 	WiFi точки: Безжична свързаност
• 	Комутатори и маршрутизатори: Мрежова инфраструктура

📞 Поддръжка
За въпроси и техническа помощ: fori@techsolutions.bg


Запази с `Ctrl+O`, излез с `Ctrl+X`.

---

## 🚀 Качи документацията в GitHub

```bash
git add docs/components.md
git commit -m "Добавена документация за компонентите на системата"
git push
