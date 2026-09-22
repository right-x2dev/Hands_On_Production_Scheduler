//main.jsx => React 프로그램 시작
//React 프로그램의ㅣ 시작점. 

//python의 from x import y랑 비슷.
//jsx 기준 import y from x...
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
//index.css에 적힌 디자인을 이 React 앱에 적용.
import './index.css'
//같은 폴더에 있는 App.jsx를 가져와라. 
import App from './App.jsx'

/*
웹페이지에서 id가 root인 장소를 찾아서
거기에 React 화면을 그려라. 
*/


/*
StrictMode: 
개발하면서 React가 이상한 코드가 있는지
조금 더 엄격하게 검사해준다. 
*/
createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
