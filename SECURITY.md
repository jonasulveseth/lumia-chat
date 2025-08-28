# Lumia Security Guide

## Lokalt nätverk säkerhet

Lumia är konfigurerad för att vara tillgänglig på lokalt nätverk (`0.0.0.0:8002`). För att säkra detta rekommenderas UFW-konfiguration.

## UFW-konfiguration

### 1. Kontrollera UFW-status

```bash
sudo ufw status
```

### 2. Aktivera UFW (om inte redan aktiverat)

```bash
sudo ufw enable
```

### 3. Konfigurera regler för Lumia

```bash
# Tillåt lokalt nätverk (192.168.x.x, 10.x.x.x, 172.16-31.x.x)
sudo ufw allow from 192.168.0.0/16 to any port 8002
sudo ufw allow from 10.0.0.0/8 to any port 8002
sudo ufw allow from 172.16.0.0/12 to any port 8002

# Tillåt localhost
sudo ufw allow from 127.0.0.1 to any port 8002
```

### 4. Verifiera regler

```bash
sudo ufw status numbered
```

Du bör se något liknande:
```
     To                         Action      From
     --                         ------      ----
[ 1] 8002/tcp                  ALLOW IN    192.168.0.0/16
[ 2] 8002/tcp                  ALLOW IN    10.0.0.0/8
[ 3] 8002/tcp                  ALLOW IN    172.16.0.0/12
[ 4] 8002/tcp                  ALLOW IN    127.0.0.1
```

## Alternativ: Mer restriktiv konfiguration

Om du vill vara mer specifik med ditt lokala nätverk:

### Hitta ditt lokala nätverk

```bash
# Hitta din lokala IP
ip addr show | grep "inet " | grep -v 127.0.0.1

# Exempel output:
# inet 192.168.1.100/24 brd 192.168.1.255 scope global dynamic noprefixroute eth0
```

### Konfigurera specifikt nätverk

```bash
# Om du är på 192.168.1.x nätverk
sudo ufw allow from 192.168.1.0/24 to any port 8002

# Om du är på 10.0.0.x nätverk
sudo ufw allow from 10.0.0.0/24 to any port 8002
```

## Säkerhetskontroll

### Testa åtkomst lokalt

```bash
# Från samma maskin
curl http://localhost:8002/health
```

### Testa åtkomst från annan maskin

```bash
# Från annan maskin på samma nätverk
curl http://192.168.1.100:8002/health  # Ersätt med din IP
```

### Kontrollera att extern åtkomst blockeras

```bash
# Testa från internet (ska blockeras)
curl http://din.public.ip:8002/health  # Ska ge timeout/error
```

## Felsökning

### Port är inte tillgänglig

```bash
# Kontrollera att Lumia lyssnar på rätt interface
netstat -tlnp | grep 8002

# Ska visa: 0.0.0.0:8002
```

### UFW-blockerar åtkomst

```bash
# Kontrollera UFW-loggar
sudo tail -f /var/log/ufw.log

# Temporärt inaktivera UFW för test
sudo ufw disable
# Testa åtkomst
sudo ufw enable
```

### Kontrollera brandväggsregler

```bash
# Lista alla regler
sudo iptables -L -n | grep 8002
```

## Rekommendationer

1. **Använd specifika IP-intervall** istället för hela lokala nätverk
2. **Övervaka loggar** regelbundet
3. **Uppdatera regler** om nätverkskonfiguration ändras
4. **Använd HTTPS** i produktion (inte implementerat än)

## Produktionssäkerhet

För produktion rekommenderas:

- HTTPS/TLS-konfiguration
- JWT-autentisering
- Rate limiting
- Loggning av åtkomst
- Regular security updates 