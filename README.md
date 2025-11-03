# Prototipo de Asistente de IA para gvsig-desktop (Jython)

> **⚠️ Repositorio Archivado: Prototipo Educativo ⚠️**
>
> Este código es el prototipo inicial descrito en la serie de artículos sobre la integración de IA en gvsig-desktop. **No está mantenido y no es para uso en producción.** Su propósito es puramente educativo y sirve como acompañamiento a los artículos que narran el viaje de desarrollo.

## Propósito de este Repositorio

Este repositorio contiene el código fuente del primer prototipo funcional que permitió usar la API de Gemini desde gvsig-desktop. Fue desarrollado en pocos días usando **Jython** y librerías estándar de Java para validar la idea principal.

El código aquí presente corresponde a la fase descrita en el artículo:
*   **"[Cómo empecé a hablar con la IA desde la aplicación de escritorio gvsig desktop en Java](https://blog.gvsig.org/2025/09/08/como-empece-a-hablar-con-la-ia-desde-la-aplicacion-de-escritorio-gvsig-desktop/)"**

## Contexto y Evolución

Aunque este prototipo fue funcional y demostró la viabilidad del concepto, sus limitaciones llevaron a una reescritura completa en Java. Esta evolución se detalla en el siguiente artículo de la serie:
*   **"[De chat a asistente, creando un conjunto de herramientas contextuales para gvsig-desktop](https://blog.gvsig.org/2025/09/15/de-chat-a-asistente-creando-un-conjunto-de-herramientas-contextuales-para-gvsig-desktop/)"**

La solución final y robusta, basada en un servidor MCP, se encuentra en un repositorio separado.

## Lo que puedes aprender de este código

*   Un ejemplo real de prototipado rápido en un entorno Java/Jython.
*   Cómo realizar llamadas a una API REST moderna (Gemini) usando solo librerías estándar de Java (`HttpURLConnection`, `javax.json`).
*   La implementación inicial de un sistema de "prompting estructurado" para forzar salidas JSON.


*   El concepto de "procesadores" para manejar diferentes tipos de respuestas de la IA.

