document.getElementById("jobForm").addEventListener("submit", function(e) {
  e.preventDefault(); // stop page refresh

  const name = document.getElementById("name").value;
  const location = document.getElementById("location").value;

  document.getElementById("result").innerText = 
    `Hello ${name}, we are searching maids/servants near ${location}...`;
});

