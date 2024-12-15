# CABRA

## Introducción

CABRA (Computarized Auditory Brainstem Response Audiometry) es un prototipo de dispositivo biomédico diseñado para la asignatura de Instrumentación Biomédica II del Instituto Tecnológico de Buenos Aires. El objetivo principal del proyecto es desarrollar un sistema de medición de potenciales evocados auditivos del tronco cerebral (ABR, Auditory Brainstem Response), que permita evaluar la integridad de las vías de conducción auditiva en el sistema nervioso central, de forma no invasiva y en tiempo real.

El sistema se compone tando de hardware como software. El hardware está formado por una placa de acondicionamiento de señales biológicas y un microcontrolador que se encarga de la adquisición de las señales. El software, por otro lado, se encarga de la interfaz con el usuario, la configuración del hardware, la reproducción de estímulos sonoros y la visualización de los resultados.

## Componentes

El sistema CABRA se compone de los siguientes elementos:

* **Hardware**: La placa de acondicionamiento de señales biológicas se encarga de amplificar y filtrar las señales biológicas provenientes del paciente. El diseño de la placa se realizó en KiCAD. El proyecto se encuentra disponible en la carpeta [PCB](https://github.com/josulas/CABRA/tree/main/PCB).

* **Microcontrolador**: El microcontrolador se encarga de la digitalización de las señales biológicas, y la comunicación con la PC. Se utilizó una ESP32-Devkit como placa de desarrollo. El firmware del microcontrolador se aloja en la carpeta [ESP32-Firmware](https://github.com/josulas/CABRA/tree/main/ESP32-Firmware).

* **Software**: El software se encarga de la interfaz con el usuario, la reproducción de estímulos sonoros y la visualización de los resultados. Este se encuentra en la carpeta [GUI](https://github.com/josulas/CABRA/tree/main/GUI). Está compuesto de una interfaz gráfica desarrollada en QT, un proceso de reproducción de estímulos sonoros desarrollado con WASAPI y un proceso de comunicación con el microcontrolador desarrollado en Python.

* **Informe**: El informe del proyecto se encuentra disponible en la carpeta [Informe](https://github.com/josulas/CABRA/tree/main/Informe). En él se detallan los objetivos, marco teórico, materiales y métodos, resultados y discusión del proyecto. Se recomienda fuertemente su lectura para una comprensión más profunda del proyecto. Las citas biográficas proporcionan un puntapié por el cual se puede comenzar a profundizar sobre el tipo de estudios que intentamos llevar a cabo.

* **Manual de Usuario**: El manual de usuario se encuentra disponible en la carpeta [Manual de Usuario](https://github.com/josulas/CABRA/tree/main/Manual%20de%20usuario). En él se detallan los pasos necesarios para la correcta utilización del sistema CABRA.

## Utilización

El Manual de Usuario proporciona una descripción detallada de como utilizar el sistema. Para una comprensión con mayor significancia, se recomienda leer la introducción y marco teóridco del informe, donde se detallan los objetivos y alcances del proyecto, así como también los fundamentos teóricos que sustentan el desarrollo del sistema y de la audiometría en general.

Para no tener que instalar todos los paquetes requeridos, se recomienda utilizar el release del proyecto, que se encuentra disponible en la sección de releases de este repositorio. Un archivo .msi guiará la instalación y configuración del sistema. Por el momento, el release solo está disponible para Windows 7 o superior, aunque se recomienda ejecutarlo en Windows 11, sistema operativo en el que fue desarrollado.

## Autores

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="33%"><a href="https://github.com/gonzagrau"><img src="https://avatars.githubusercontent.com/u/107513203?v=4" width="200px;" alt="Gonzalo Andrés Grau"/><br /><sub><b>Gonzalo Andrés Grau</b></sub></a><br/></td>
      <td align="center" valign="top" width="33%"><a href="https://github.com/Lucasfranzi"><img src="https://avatars.githubusercontent.com/u/107051293?v=4" width="200px;" alt="Lucas Franzi"/><br /><sub><b>Lucas Franzi</b></sub></a><br /></td>
      <td align="center" valign="top" width="33%"><a href="https://github.com/josulas"><img src="https://avatars.githubusercontent.com/u/89985451?v=4" width="200px;" alt="Josue Francisco Laszeski"/><br /><sub><b>Josue Francisco Laszeski</b></sub></a><br /></td>
    </tr>
  </tbody>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->
<!-- ALL-CONTRIBUTORS-LIST:END -->

## Agradecimientos

Damos especial reconocimiento a la cátedra de la asignatura, por su constante apoyo en el desarrollo del proyecto y su continua disponibilidad para resolver nuestras inquietudes:

* **Titular**: Prof. Ing. Gustavo Panza [Linkedin](https://www.linkedin.com/in/gustavo-panza-507836271/).
* **JTP**: Ing. Franco Pérez Rivera [Linkedin](https://www.linkedin.com/in/franco-perez-rivera-2378871b6/).
* **JTP**: Ing. Ramón J. Igarreta [Linkedin](https://www.linkedin.com/in/ramon-javier-igarreta-711b27271/).
* **Ayudante**: Bianca J. Soto Acosta [Linkedin](https://www.linkedin.com/in/bianca-jocelyn-soto-acosta-005990239/).

También queremos dar mención especial a la [Mutualidad Argentina de Hipoacusia](https://mah.org.ar/) por prestarnos el terminal de conducción ósea, que fue utilizado para la validación del sistema al operar en tal modalidad.
