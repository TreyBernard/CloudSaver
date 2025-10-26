// src/results.jsx
import React from 'react';
import { Bar } from 'react-chartjs-2';
import {Chart as ChartJS,CategoryScale,LinearScale,BarElement,Title,Tooltip,Legend,} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

const Results = ({ results }) => {
  const data ={
    labels: results.map((item) => item.service),
    datasets:[
      {
        label: 'Savings ($)',
        data: results.map((item) => item.savings),
        backgroundColor: 'rgba(75, 192, 192, 0.6)',
        borderColor: 'rgba(75, 192, 192, 1)',
        borderWidth: 1,
      },
    ],
  };

  const options= {
    responsive: true,
    plugins:{
      legend: { position: 'top' },
      title: { display: true, text: 'Optimization Results' },
    },
  };

  return (
    <div className="mt-6 w-full max-w-2xl bg-white rounded-lg shadow p-6">
      <h2 className="text-2xl font-semibold mb-4">Optimization Results</h2>
      <Bar data={data} options={options}/>
    </div>
  );
};

export default Results;
