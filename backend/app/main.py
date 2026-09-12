#FastAPI 가져온다.
from fastapi import FastAPI

#우리가 만들 웹 서버 애플리케이션 객체를 생성
app = FastAPI()

#사용자가 / 주소로 GET요청을 보내면 바로 아래 함수를 실행. 
@app.get("/")
def root():
    return {"message": "Production Scheduler API"}