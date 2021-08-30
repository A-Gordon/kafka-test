# Kafka data assessment

## Build
I built the container locally and pushed to my docker hub repo, it is publicly available so you can pull directly from there or you can build it yourself with

```
docker build -t ${repo}/${container_name}:${version} .
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

The instructions below assume that you want to deploy kafka and mongodb aswell as the application, if that is not the case and you wish to integrate either kafka or mongodb from elsewhere that is possible. Feel free to ignore the respective instructions for the service that you wish to manage yourself. 

Start minikube
```
minikube start
```

Kafka and Mongodb installed via helm

If you change the name of either of the helm releases or the Kubernetes namespace then you will need to change the values further along in the deployment. 
This example uses the names kafka and mongodb for the respective services and is deployed into the default namespace. 
```
helm repo add bitnami https://charts.bitnami.com/bitnami
helm install kafka bitnami/kafka --namespace=default
helm install mongodb bitnami/mongodb --namespace=default
```

The helm charts will detail how to retrieve the connection details when you deploy. 

To create the secret for the MongoDB URI run:
```
export MONGODB_ROOT_PASSWORD=$(kubectl get secret --namespace default mongodb -o jsonpath="{.data.mongodb-root-password}" | base64 --decode)

kubectl create secret generic mongodb-uri --from-literal=MONGODB_URI="mongodb://root:${MONGODB_ROOT_PASSWORD}@mongodb:27017" --namespace default

```

Alternatively you can define the connection details as environment variables like so.

```
  - name: KAFKA_BOOTSTRAP_BROKER
    value: "kafka.default.svc.cluster.local:9092"
  - name: MONGODB_URI 
    value: "mongodb://root:password@mongodb:27017"
```

Configure the kafka and mongodb connection details in the yaml files.

kafka-producer-deploy.yaml

The producer connects directly to the brokers and has no need for mongodb credentials, it is already configured with the correct broker name. Change this if  you are using a different kafka instance or namespace. 
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

To verify the installation you can check that all the pods are running successfully. 
```
kubectl get pods
NAME                              READY   STATUS    RESTARTS   AGE
kafka-0                           1/1     Running   0          23h
kafka-client                      1/1     Running   0          24h
kafka-consumer-5577dffb7d-mr4v5   1/1     Running   0          18m
kafka-producer-747488775d-7kpq5   1/1     Running   0          18m
kafka-zookeeper-0                 1/1     Running   0          23h
mongodb-f49679fc5-8fq4p           1/1     Running   0          10m
```

To iew the logs of the applications
```
CONSUMER_POD=$(kubectl get pods --field-selector=status.phase=Running -l app=kafka-consumer -o jsonpath='{.items[*].metadata.name}'); kubectl logs $CONSUMER_POD
```

```
PRODUCER_POD=$(kubectl get pods --field-selector=status.phase=Running -l app=kafka-producer -o jsonpath='{.items[*].metadata.name}'); kubectl logs $PRODUCER_POD
```