import psutil
import subprocess
import socket


def obtener_cpu():
    uso_cpu = psutil.cpu_percent(interval=1)
    nucleos_fisicos = psutil.cpu_count(logical=False)
    nucleos_logicos = psutil.cpu_count(logical=True)

    return {
        "uso_cpu": uso_cpu,
        "nucleos_fisicos": nucleos_fisicos,
        "nucleos_logicos": nucleos_logicos
    }


def obtener_ram():
    ram = psutil.virtual_memory()

    total_gb = ram.total / (1024 ** 3)
    usada_gb = ram.used / (1024 ** 3)
    disponible_gb = ram.available / (1024 ** 3)

    return {
        "total_gb": round(total_gb, 2),
        "usada_gb": round(usada_gb, 2),
        "disponible_gb": round(disponible_gb, 2),
        "porcentaje": ram.percent
    }


def obtener_disco():
    disco = psutil.disk_usage("/")

    total_gb = disco.total / (1024 ** 3)
    usado_gb = disco.used / (1024 ** 3)
    libre_gb = disco.free / (1024 ** 3)

    return {
        "total_gb": round(total_gb, 2),
        "usado_gb": round(usado_gb, 2),
        "libre_gb": round(libre_gb, 2),
        "porcentaje": disco.percent
    }


def obtener_ip_local():
    """
    Obtiene la IP real de red, por ejemplo 192.168.x.x.
    Evita devolver 127.0.0.1 o 127.0.1.1.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(3)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()

        if ip and not ip.startswith("127."):
            return ip

    except Exception:
        pass

    try:
        interfaces = psutil.net_if_addrs()

        for _, direcciones in interfaces.items():
            for direccion in direcciones:
                if direccion.family == socket.AF_INET:
                    ip = direccion.address

                    if ip and not ip.startswith("127."):
                        return ip

    except Exception:
        pass

    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)

        if ip and not ip.startswith("127."):
            return ip

    except Exception:
        pass

    return "No disponible"


def probar_internet():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False


def obtener_red():
    ip_local = obtener_ip_local()
    estadisticas = psutil.net_io_counters()

    enviado_mb = estadisticas.bytes_sent / (1024 ** 2)
    recibido_mb = estadisticas.bytes_recv / (1024 ** 2)

    internet = probar_internet()

    return {
        "ip_local": ip_local,
        "internet": internet,
        "enviado_mb": round(enviado_mb, 2),
        "recibido_mb": round(recibido_mb, 2)
    }


def obtener_temperatura():
    """
    Intenta obtener temperatura usando psutil.
    Si no hay sensores disponibles, intenta usar el comando sensors.
    """
    try:
        temps = psutil.sensors_temperatures()

        if temps:
            temperaturas = []

            for nombre_sensor, entradas in temps.items():
                for entrada in entradas:
                    if entrada.current:
                        temperaturas.append({
                            "sensor": nombre_sensor,
                            "label": entrada.label,
                            "temp": entrada.current
                        })

            if temperaturas:
                temp_principal = temperaturas[0]["temp"]
                return {
                    "disponible": True,
                    "temperatura": round(temp_principal, 1),
                    "detalle": temperaturas
                }

    except Exception:
        pass

    try:
        resultado = subprocess.run(
            ["sensors"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if resultado.returncode == 0 and resultado.stdout:
            return {
                "disponible": True,
                "temperatura": None,
                "detalle_texto": resultado.stdout
            }

    except Exception:
        pass

    return {
        "disponible": False,
        "temperatura": None,
        "detalle": []
    }


def resumen_estado_sistema():
    cpu = obtener_cpu()
    ram = obtener_ram()
    disco = obtener_disco()
    red = obtener_red()
    temp = obtener_temperatura()

    texto = (
        f"Estado del sistema. "
        f"CPU al {cpu['uso_cpu']} por ciento. "
        f"RAM usada: {ram['usada_gb']} de {ram['total_gb']} gigabytes, equivalente al {ram['porcentaje']} por ciento. "
        f"Disco usado: {disco['usado_gb']} de {disco['total_gb']} gigabytes, con {disco['libre_gb']} gigabytes libres. "
    )

    if red["internet"]:
        texto += f"La conexión a internet está activa. Tu IP local es {red['ip_local']}. "
    else:
        texto += f"No detecto conexión a internet. Tu IP local es {red['ip_local']}. "

    if temp["disponible"] and temp["temperatura"] is not None:
        texto += f"La temperatura principal es de {temp['temperatura']} grados Celsius."
    elif temp["disponible"]:
        texto += "Detecté sensores de temperatura, pero el detalle está disponible solo en terminal."
    else:
        texto += "No pude leer sensores de temperatura."

    return texto


def resumen_ram():
    ram = obtener_ram()

    return (
        f"Tienes {ram['total_gb']} gigabytes de RAM. "
        f"Actualmente se están usando {ram['usada_gb']} gigabytes, "
        f"y quedan disponibles {ram['disponible_gb']} gigabytes."
    )


def resumen_cpu():
    cpu = obtener_cpu()

    return (
        f"El procesador está usando {cpu['uso_cpu']} por ciento. "
        f"Tiene {cpu['nucleos_fisicos']} núcleos físicos "
        f"y {cpu['nucleos_logicos']} hilos lógicos."
    )


def resumen_disco():
    disco = obtener_disco()

    return (
        f"El disco principal tiene {disco['total_gb']} gigabytes. "
        f"Estás usando {disco['usado_gb']} gigabytes, "
        f"y quedan libres {disco['libre_gb']} gigabytes."
    )


def resumen_red():
    red = obtener_red()

    if red["internet"]:
        estado = "La conexión a internet está activa."
    else:
        estado = "No detecto conexión a internet."

    return (
        f"{estado} "
        f"Tu IP local es {red['ip_local']}. "
        f"Datos enviados: {red['enviado_mb']} megabytes. "
        f"Datos recibidos: {red['recibido_mb']} megabytes."
    )


def resumen_ip():
    red = obtener_red()

    if red["ip_local"] == "No disponible":
        return "No pude detectar tu IP local de red."

    return f"Tu IP local es {red['ip_local']}."


def resumen_temperatura():
    temp = obtener_temperatura()

    if temp["disponible"] and temp["temperatura"] is not None:
        return f"La temperatura principal detectada es de {temp['temperatura']} grados Celsius."

    if temp["disponible"]:
        return "Detecté sensores de temperatura, pero no pude resumirlos automáticamente. Revisa el detalle con el comando sensors en terminal."

    return "No pude leer la temperatura. Puede que necesites configurar lm-sensors."
