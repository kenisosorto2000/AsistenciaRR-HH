document.addEventListener("DOMContentLoaded", function () {
    const mensaje = document.getElementById("mensaje-corte");
    const hoy = new Date();
    const dia = hoy.getDate();
    const mes = hoy.getMonth();
    const anio = hoy.getFullYear();

    const corte1 = 9;
    const corte2 = 24;

    let mensajeTexto = "";
    let diasRestantes = 0;

    if (dia === corte1 || dia === corte2) {
        mensajeTexto = `📌 Hoy es día de corte (${dia} del mes).`;
        mensaje.style.backgroundColor = "#dc2626"; // rojo
        mensaje.style.color = "white";
    } else if (dia < corte1) {
        diasRestantes = corte1 - dia;
        mensajeTexto = `⏳ Faltan ${diasRestantes} día${diasRestantes === 1 ? '' : 's'} para el corte del día ${corte1}.`;
    } else if (dia > corte1 && dia < corte2) {
        diasRestantes = corte2 - dia;
        mensajeTexto = `⏳ Faltan ${diasRestantes} día${diasRestantes === 1 ? '' : 's'} para el corte del día ${corte2}.`;
    } else {
        const proximoCorte = new Date(anio, mes + 1, corte1);
        const diferenciaMs = proximoCorte - hoy;
        diasRestantes = Math.ceil(diferenciaMs / (1000 * 60 * 60 * 24));
        mensajeTexto = `📅 Ya pasaron los días de corte. Faltan ${diasRestantes} día${diasRestantes === 1 ? '' : 's'} para el próximo corte (${corte1} del siguiente mes).`;
    }

    // Estilo dinámico según días restantes
    if (diasRestantes > 5) {
        mensaje.style.backgroundColor = "#10b981"; // verde
        mensaje.style.color = "white";
    } else if (diasRestantes >= 3) {
        mensaje.style.backgroundColor = "#facc15"; // amarillo
        mensaje.style.color = "#1f2937"; // gris oscuro
    } else if (diasRestantes >= 1) {
        mensaje.style.backgroundColor = "#f97316"; // naranja
        mensaje.style.color = "white";
    }

    mensaje.textContent = mensajeTexto;
});