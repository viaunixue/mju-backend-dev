# Load Balancer

#### 트래픽 입력을 밴엔드 서버들에 골고루 분산하는 작업
> 참고 : server farm or server pool &rarr; 동일한 작업을 하는 서버 집단

### 효과
* Efficiency : 클라이언트 요청 혹은 네트워크 트래픽을 골고루 분산시켜 서버 자원을 효과적으로 사용합니다.

* Availability : 살아있는 서버에게만 요청을 전달함으로써 availability 를 증대합니다. <br>
&rarr; 서비스가 클라이언트에게 얼마나 죽지 않고 살아있는가? <br> 
ex) 99% availability &rarr; 1년 중 동작하지 않는 시간이 8.77 시간 이내

* Flexibility & Scalability : 클라이언트 요청 규모에 따라 운용 서버 대수를 조정 가능합니다.

## OSI 모델의 Layer 따른 로드 밸런싱

* OSI 모델의 각 layer 별로 로드 밸런싱이 가능합니다. <br>
ex) Layer 3 LB : IP header 기준으로 분산 <br>
    &nbsp; &nbsp; &nbsp; Layer 7 LB : Application header 를 참고해서 분산

## 하드웨어 로드 밸런싱 & 소프트웨어 로드 밸런싱

* 로드 밸런싱 기능은 하드웨어 장비로도 구현할 수 있고, 소프트웨어로도 구현할 수 있습니다.

1. 네트워크 경로 중간에서 트래픽을 받아
2. 특정 layer 헤더를 살펴보고
3. 적절히 트래픽을 보냄 ( = switching )

### 하드웨어 로드 밸런서
* 특화된 하드웨어 사용으로 고성능
* 가격 비싸고 로드 밸런싱 업데이트가 어려움

### 소프트웨어 로드 밸런서
* 범용 CPU 에 Linux 같은 OS 를 올리고 소프트웨어를 실행
* 트래픽 처리 성능은 떨어질 수 있으나 로드 밸런싱 방식 변경이 용이
* Nginx, HAProxy 등의 설치형 솔루션 및 AWS 의 LB 처럼 클라우드 솔루션 존재

## 로드 밸런싱 알고리즘
* 요청/트래픽을 전달할 서버를 선택하는 방식에는 다음과 같은 것들이 있습니다.

### Round-robin 
순서대로 한번씩 서버를 선택

### Hash 
클라이언트 IP 처럼 미리 정한 key 에 따라 hash 한 결과로 서버를 선택

### Least connections 
현 시점에서 가장 적은 연결의 서버를 선택

### Least time 
평균 응답 시간이 가장 빠른 서버를 선택

### Random
임의의 서버를 선택

## 로드 밸런서 사용 시 구조도

* 로드 밸런서가 중간에서 모든 트래픽을 다 받아야 합니다.

![lb_1](/asset/img/load_balance.png)

## 로드 밸런서 적용 대상

* 전체 서비스 구성도에서 `어떤 서버들에만 로드 밸런싱을 적용한다` 같은 제약은 없습니다.

* 백엔드 시스템을 "퉵 서버 + 앱 서버" 형태로 구성한 경우,
웹 서버도 pool 로 구성한 뒤 로드 밸런서를 붙일 수 있고, 앱 서버도 pool로 구성한 뒤 별도의 로드 밸런서를 붙일 수 있음 <br>

    ex) Nginx + uWSGI(Flask) 구조 <br>

    ![lb_2](/asset/img/load_balance_2.png)

## 로드 밸런서 적용 시 문제점

* 클라이언트를 기억하는 `stateful` 한 서버에서는 같은 클라이언트로부터의 요청을 동일한 서버에게 전달해야 합니다.

    ```
    게임 서버를 만들었는데, 게임 서버 1번과 통신하고 있다가 다음 요청을 했더니 
    2번한테 갔다고 한다면 여태까지 했던 것들을 알 방법이 없습니다.
    ```

* 서버가 `stateless` 한 경우도, 서버들이 매번 DB에서 클라이언트 정보를 읽어오는 것은 DB에 과부하를 주게 됩니다. 이 때문에 일부 정보를 caching 하는 경우가 빈번한데, 이 경우 같은 클라이언트를 같은 서버가 처리하지 않을 경우 성능 문제가 발생합니다.

    ```
    이러한 문제를 막을 방법은 DB에서 읽어온 후 그 서버가 caching을 하면 됩니다. 
    cache 라고 하면 반드시 따라오는 건 오래된 데이터 입니다. 
    이 경우는 만약 A 라는 클라이언트와 통신하고 있었고 A 가 cache를 했습니다. 
    다음 번 요청이 B에게 가고 B도 갱신을 통한 업데이트가 되었습니다. 
    세번째 요청이 다시 A에게 간다고 치면 A가 cache 한 데이터를 쓰게 되면 문제가 됩니다. 
    그래서 보통 caching을 할꺼면 항상 동일한 서버에 mapping을 해주어야 합니다. 
    그렇지 않을 경우 cache가 의미가 없게 됩니다.
    ```

* 세션 지속성 (Session persistence 또는 sticky session)

    * 클라이언트 session 시간 동안은 같은 클라이언트는 같은 서버와 통신하게 하는 것입니다.

    * 헤더에서 session을 구분할 수 있는 정보가 있어야 합니다. (L3의 경우 IP, L7은 HTTP 헤더)

## EC2 &rarr; 이미지 &rarr; AMI (Amazon Machine Image)

* 가상 서버 이미지
    * 아마존 제공
    * Marketplace 를 통해 판매자 제공 (별도 요금 추가)
    * 직접 만드는 것도 가능

* 새 인스턴스 (= 가상서버) 를 띄울 때 AMI 를 이용함
    * 보통은 아마존이 제공하는 Ubuntu 나 CentOS AMI 를 이용
    * 그러나 auto-scaling 에서는 “우리 서버” 를 복제해서 바로 활용할 수 있어야 하므로 “우리 서버” 의 AMI 를 만들어 두는 것이 일반적임

## EC2 &rarr; 인스턴스 &rarr; 시작 템플릿

* 인스턴스를 생성할 때는 다양한 옵션이 존재함

    > 예: 사용할 AMI, 인스턴스 타입, 디스크 용량, 사용할 서브넷, SSH public key 등등
이 옵션을 미리 정해둔 것을 “시작 템플릿” 이라고 함

## EC2 &rarr; 로드 밸런싱 &rarr; 대상 그룹

* 로드 밸런서가 트래픽을 전달할 server pool 의미함

    > Server pool 이므로 서버들은 모두 동일한 포트를 통해 동작한다고 가정

    ![elb_1](/asset/img/elb_1.png)



## 대상 그룹 내 서버들의 Health Check

* 대상 그룹 내 동작하지 않는 서버에게 요청을 전달하면 안되므로
서버가 살아있는지 확인 해야되는데 이를 “health check” 라고 함

* 특정 port, HTTP URL 의 접근 가능 여부로 확인

## EC2 &rarr; 로드 밸런싱 &rarr; 로드 밸런서

* Application Load Balancer → L7 로드 밸런서

* Network Load Balancer → L4 로드 밸런서

* 실습에서는 Application Load Balancer 를 사용함 <br>
&rarr; LB 가 사용할 “대상 그룹” 을 지정하는 방식을 사용함 <br>
&rarr; LB 는 서버와 다른 port 와 보안그룹을 가질 수 있음
    ![elb_2](/asset/img/elb_2.png)

* Application Load Balancer 는 IP 가 아니라 DNS 이름으로 접근함 <br>
&rarr; LB 가 어떤 서버에 접근하는지를 알기 때문에 각 서버들에는 Elastic IP 를 부여할 필요가 없음

    ![elb_3](/asset/img/elb_3.png)

## EC2 &rarr; Auto Scaling &rarr; Auto Scaling 그룹

* 로드 밸런서가 사용하는 “대상 그룹” 을 고정적으로 운용할 수도 있지만,
많은 경우 요청/트래픽 양에 따라 서버 대수를 조정하고 싶은 경우가 있음

* 이 때 일정 조건 (예: CPU 사용량, 요청 수) 등에 따라
자동으로 “대상 그룹” 에 서버를 추가/삭제 해주는 기능이 “auto scaling” 임

* Auto scaling 은 DDoS 같은 공격에도 서버 대수를 늘리므로 과도한 요금을 주의해야 함