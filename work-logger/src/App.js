import React, { useState, useEffect } from "react";
import axios from "axios";
import logo from './logo.svg';
import './App.css';

function App() {
  const [msg, setMsg] = useState();
  useEffect(async () => {
    try {
      const res = await axios.get("/welcome");
      console.log(res);
      setMsg(res.data);
    } catch (error) {
      console.log(error);
    }
  }, []);
  console.log(msg);

  return (
    <div className="App">
        <p>
          {msg}
        </p>
    </div>
  );
}

export default App;
