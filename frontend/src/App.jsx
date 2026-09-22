//App.jsx => 실제 화면 내용 + 동작

//useState: 화면에서 기억해야 하는 값을 만드는 기능
import { useState } from "react";
import "./App.css";

//컴포넌트: 화면 하나를 만드는 함수. 
function App() {
  //selectedAlgorithm: 현재 선택된 알고리즘 값
  //setSelectedAlgorithm(...): 그 값을 바꾸는 함수
  const [selectedAlgorithm, setSelectedAlgorithm] = useState("SPT");
  //초기값이 "-"
  const [resultAlgorithm, setResultAlgorithm] = useState("-");

  // () => {} 
  // 화살표 함수 문법. 
  /*
  1. 데이터 변경
  2. React가 감지
  3. 화면 자동 변경
  */
  const handleRunScheduling = () => {
    setResultAlgorithm(selectedAlgorithm);
  };




  return (
    //div: 여러 요소를 묶는 상자.
    //header: 화면 위쪽 제목느낌을 만드는 부분
    //main: 웹페이지의 주요 내용 영역. 
    //section: 화면의 한 구역. 
    //select: 드롭다운메뉴
    //value: 현재 드롭다운 값이 selectedAlgorithm이라는 뜻
    //React JSX 안에서 JavaScript 값 사용할때, {} 사용.
    //onChange: 사용자가 드롭다운 값을 바꾸면 실행하라
    //option: 드롭다운 선택 항목. 
    //onClick: 클릭했을때.
    <div className="app">
      <header className="header">
        <h1>Production Scheduler</h1>
        <p>Flexible Job Shop Scheduling System</p>
      </header>

      <main className="main">
        <section className="card">
          <h2>Scheduling Algorithm</h2>

          <select
            value={selectedAlgorithm}
            //드롭다운에서 다른 알고리즘 고르면 선택값 저장.
            //버튼 클릭시 아래 함수가 실행되서 Result쪽이 바뀌는 구조.
            onChange = {(e) => setSelectedAlgorithm(e.target.value)}
          >
            <option value="SPT">SPT</option>
            <option value="EDD">EDD</option>
            <option value="FIFO">FIFO</option>
            <option value="Genetic Algorithm">Genetic Algorithm</option>
            <option value="Simulated Annealing">Simulated Annealing</option>
            <option value="PSO">PSO</option>
            <option value="DQN">DQN</option>
          </select>

          
          <button onClick={handleRunScheduling}>
            Run Scheduling
            </button>
        </section>

        <section className="card">
          <h2>Result</h2>

          <p>Makespan: -</p>
          <p>Selected Algorithm: {resultAlgorithm}</p>
        </section>
      </main>
    </div>
  );
}
// 다른 파일에서 App을 가져갈 수 있게 내보내는 것. 
//App.jsx에서 App 내보내면, main.jsx에서 App 가져옴.
export default App;