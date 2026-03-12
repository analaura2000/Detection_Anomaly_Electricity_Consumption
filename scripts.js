let currentPage = 1;
const rowsPerPage = 10;
let predictionsData = [];
const maxPagesToShow = 5; // Maximum page indices visible at once

// Function to process and upload data
async function processData() {
    const archivoInput = document.getElementById('archivo');
    const sheetNameInput = document.getElementById("sheet_name");
    
    if (!archivoInput.files.length) {
        alert("Please select a file.");
        return;
    }

    let formData = new FormData();
    formData.append("archivo", archivoInput.files[0]);
    
    // Get sheet name from the sheet-selection button
    const selectedSheetName = sheetNameInput && sheetNameInput.value ? sheetNameInput.value : null;
    // If a sheet name was chosen, append it; otherwise skip
    if (selectedSheetName) {
        formData.append("sheet_name", selectedSheetName);
    }

    fetch("/predict", {
        method: "POST",
        body: formData
    })
    
    .then(response => response.json())
    .then(data => {
        predictionsData = data; // store data for pagination

        if (data.error) {
            alert(`Error: ${data.error}`);
            return;
        }

        // Clear previous results
        const resultadosTabla = document.getElementById("resultados").getElementsByTagName("tbody")[0];
        resultadosTabla.innerHTML = "";

        // Add new results
        displayPage(currentPage);
    })
    .catch(error => console.error("Error processing data:", error));
}

// Function to display data in the table
function displayPage(page) {
    const start = (page - 1) * rowsPerPage;
    const end = start + rowsPerPage;
    const tableBody = document.querySelector("#resultados tbody");
    tableBody.innerHTML = "";

    predictionsData.slice(start, end).forEach(prediction => {
        const row = document.createElement("tr");
        row.innerHTML = `<td>${prediction.id}</td><td>${prediction.prediction}</td>`;
        tableBody.appendChild(row);
    });

    setupPagination();
}

// Function to setup pagination with limited range and "..." buttons
function setupPagination() {
    const pagination = document.getElementById("pagination");
    pagination.innerHTML = "";
    const totalPages = Math.ceil(predictionsData.length / rowsPerPage);

    let startPage = Math.max(currentPage - Math.floor(maxPagesToShow / 2), 1);
    let endPage = Math.min(startPage + maxPagesToShow - 1, totalPages);

    if (endPage - startPage < maxPagesToShow - 1) {
        startPage = Math.max(endPage - maxPagesToShow + 1, 1);
    }

    // "..." button to jump back a block of pages
    if (startPage > 1) {
        const prevBlock = document.createElement("button");
        prevBlock.innerText = "...";
        prevBlock.addEventListener("click", () => {
            currentPage = Math.max(startPage - maxPagesToShow, 1);
            displayPage(currentPage);
        });
        pagination.appendChild(prevBlock);
    }

    // Page index buttons
    for (let i = startPage; i <= endPage; i++) {
        const button = document.createElement("button");
        button.innerText = i;
        button.className = (i === currentPage) ? "active" : "";
        button.addEventListener("click", () => {
            currentPage = i;
            displayPage(currentPage);
        });
        pagination.appendChild(button);
    }

    // "..." button to advance a block of pages
    if (endPage < totalPages) {
        const nextBlock = document.createElement("button");
        nextBlock.innerText = "...";
        nextBlock.addEventListener("click", () => {
            currentPage = Math.min(endPage + 1, totalPages);
            displayPage(currentPage);
        });
        pagination.appendChild(nextBlock);
    }
}

// Function to export to Excel
function exportExcel() {
    const ws = XLSX.utils.json_to_sheet(predictionsData);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "Predictions");
    XLSX.writeFile(wb, "predictions.xlsx");
}

// Function to select the sheet from the Excel file
async function selectSheet() {
    const archivoInput = document.getElementById('archivo');
    if (!archivoInput.files.length) {
        alert("Please select a file.");
        return;
    }

    const file = archivoInput.files[0];
    const reader = new FileReader();
    reader.onload = function(e) {
        const data = new Uint8Array(e.target.result);
        const workbook = XLSX.read(data, {type: 'array'});

        // Clear the sheet-name input and populate select options
        const sheetSelect = document.getElementById("sheet_name");
        sheetSelect.innerHTML = ""; // clear previous options
        // Add each sheet as an option in the select
        workbook.SheetNames.forEach(sheet => {
            const option = document.createElement("option");
            option.value = sheet;
            option.textContent = sheet;
            sheetSelect.appendChild(option);
        });

        if (workbook.SheetNames.length === 1) {
            // If there's only one sheet in the file, select it and hide the selector
            sheetSelect.value = workbook.SheetNames[0];
            sheetSelect.style.display = 'none';
            // Call processData automatically to skip the selection page
            processData();
        } else {
            // Show the selector so the user can pick
            sheetSelect.style.display = 'block';
        }
    };
    reader.readAsArrayBuffer(file);
}

// Attach change event to file input to auto-select sheet
document.getElementById('archivo').addEventListener('change', selectSheet);