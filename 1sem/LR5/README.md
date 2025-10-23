# Лабораторная работа №5

# Задание

На основе продемонстрированного [примера](https://colab.research.google.com/drive/1ebY2plg9D_QupFdHVBtVqQXO7XpWy7At?usp=sharing) и [мини-проекта](https://github.com/nzhukov/grpc_lib_rec_demo) с реализацией двух сервисов (рекомендация книг), реализуйте приложение, аналогичное приложение из задания 4, с использованием gRPC, protobuf.  Предоставьте ссылку на репозиторий GitHub со всеми необходимыми компонентами для развертывания. При возможности, разверните словарь на публичном сервере в вебе. 

В репозитории отразите отчет с помощью файла с разметкой Markdown, где демонстрировался бы процесс развертывания и работы сервиса.

Формулировка задания

Создать полный глоссарий употребляемых терминов по какой-то области (допустим, Python) и спроектировать доступ к нему в виде  Web API в докер-контейнере по образцу brendanburns/dictionary-server (или в иной форме отчуждения/контейнеризации, допускающей быстрое развёртывание на произвольной  платформе). 


---

# Решение

Создали файл .proto (glossary.proto), на его основе сгенерировали файлы для передачи данных glossary_pb2.py, glossary_pb2_grpc.py. Работа с SQLite базой данных
содержится в файле database.py. Основной файл (gRPC + Web API) в main.py. Провели сборку через docker и запустили. 

Во время работы были трудности с сопоставлением задания ЛР 4, сборкой docker (контейнер не запускался) и с недопониманием как развертывать на публичном сервере в вебе.

<img width="1804" height="801" alt="image" src="https://github.com/user-attachments/assets/8ae4136e-1889-470d-8bc4-a290d352101e" />


<img width="1626" height="58" alt="image" src="https://github.com/user-attachments/assets/5836f35a-0fb8-4c47-aa8d-3e0b4562cefe" />

<img width="973" height="535" alt="image" src="https://github.com/user-attachments/assets/55da3dce-0426-458b-bd13-567fb26bc45e" />

<img width="1449" height="657" alt="image" src="https://github.com/user-attachments/assets/925dd027-0448-4ee2-8b8d-e4b2ec538d7b" />


