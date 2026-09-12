여기서 한 가지 먼저 정확히 짚자. FIFO는 “어떤 작업을 먼저 처리할지”에 대한 규칙이지, FJSP에서 여러 후보 Machine 중 어느 Machine을 선택할지까지 정해주는 알고리즘은 아니야.
그래서 V1에서는 이렇게 정의하자.
Job은 입력된 순서대로 FIFO 처리하고, 각 Operation은 가장 빨리 작업을 끝낼 수 있는 Machine에 배정한다.

즉 J1 → J2 → J3 순서로 보되, Machine은 Earliest Completion Time 기준으로 고른다.
