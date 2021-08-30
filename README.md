# Schiphol data assessment

## Build
I built the container locally and pushed to my docker hub repo, it is publicly available so you can pull directly from there or you can build it yourself with

```
docker build -t agordon/kafka-test:0.0.3 .
```

## Deployment
I deployed this locally on a Mac using minikube, the installation may differ on different devices. 

### Requirements
* Helm
* Minikube
* Kubectl 


### Versions

```
% helm version                                                                                                    
version.BuildInfo{Version:"v3.5.4", GitCommit:"1b5edb69df3d3a08df77c9902dc17af864ff05d1", GitTreeState:"dirty", GoVersion:"go1.16.3"}
```

```
% kubectl version
Client Version: version.Info{Major:"1", Minor:"20", GitVersion:"v1.20.0", GitCommit:"af46c47ce925f4c4ad5cc8d1fca46c7b77d13b38", GitTreeState:"clean", BuildDate:"2020-12-08T17:59:43Z", GoVersion:"go1.15.5", Compiler:"gc", Platform:"darwin/amd64"}
```

```
% minikube version                                                                                               
minikube version: v1.22.0
commit: a03fbcf166e6f74ef224d4a63be4277d017bb62e
```

Assuming you dont have minikube
```
curl -LO https://storage.googleapis.com/minikube/releases/v1.22.0/minikube-darwin-amd64
sudo install minikube-darwin-amd64 /usr/local/bin/minikube
```

### Instructions
Start minikube
```
minikube start
```

Kafka and Mongodb installed via helm
```
helm repo add bitnami https://charts.bitnami.com/bitnami
helm install kafka bitnami/kafka
helm install mongodb bitnami/mongodb
```

The helm charts will detail how to retrieve the connection details when you deploy. 

To create the secret for the MongoDB URI run:
```
export MONGODB_ROOT_PASSWORD=$(kubectl get secret --namespace default mongodb -o jsonpath="{.data.mongodb-root-password}" | base64 --decode)

kubectl create secret generic mongodb-uri --from-literal=MONGODB_URI="mongodb://root:${MONGODB_ROOT_PASSWORD}@mongodb:27017" --namespace default

```

Alternatively you can define the connection details as environment variables like so 

```
  - name: KAFKA_BOOTSTRAP_BROKER
    value: "kafka.default.svc.cluster.local:9092"
  - name: MONGODB_URI 
    value: "mongodb://root:password@mongodb:27017"
```

Configure the kafka and mongodb connection details in the yaml files.

kafka-producer-deploy.yaml

The producer connects directly to the brokers and has no need for mongodb credentials, it is already configured with the correct broker name. Change this if  you are using a different kafka instance. 
``` 
  - name: KAFKA_BOOTSTRAP_BROKER
    value: "kafka-0.kafka-headless.default.svc.cluster.local:9092"
```


kafka-consumer-deploy.yaml

The consumer is able to connect to the Kubernetes service, it is already configured but once again change if connecting to different endpoints. 

``` 
  - name: KAFKA_BOOTSTRAP_BROKER
    value: "kafka.default.svc.cluster.local:9092"
  - name: MONGODB_URI 
    value: "mongodb://root:password@mongodb:27017"
```

Deploy to Kubernetes
```
kubectl apply -f kafka-consumer-deploy.yaml
kubectl apply -f kafka-producer-deploy.yaml
```

At this stage you should have a working kafka cluster, mongodb cluster and two pods, the producer and consumer respectively. 

For the purpose of this assessment I have purposefully kept mongo and kafka as simple as possible and they are deployed in a single node instance. 