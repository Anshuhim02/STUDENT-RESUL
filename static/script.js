document.addEventListener('DOMContentLoaded', function() {
    // ------------------------------------------
    // DYNAMIC SUBJECT ROWS (Add/Edit Page)
    // ------------------------------------------
    const generateBtn = document.getElementById('generateSubjectsBtn');
    const subjectCount = document.getElementById('subjectCount');
    const subjectRows = document.getElementById('subjectRows');
    const calculateBtn = document.getElementById('calculateBtn');

    if (generateBtn) {
        generateBtn.addEventListener('click', function() {
            const count = parseInt(subjectCount.value);
            if (!count || count < 1) {
                alert('Please enter a valid number of subjects (at least 1).');
                return;
            }
            let html = '';
            for (let i = 0; i < count; i++) {
                html += `
                    <tr>
                        <td><input type="text" name="subject_name[]" class="form-control" placeholder="e.g. Math" required></td>
                        <td><input type="number" name="obtained[]" class="form-control obtained" placeholder="Obtained" required min="0"></td>
                        <td><input type="number" name="total[]" class="form-control total" placeholder="Total" required min="1"></td>
                        <td class="text-center"><button type="button" class="btn btn-sm btn-outline-danger remove-row"><i class="fas fa-times"></i></button></td>
                    </tr>
                `;
            }
            subjectRows.innerHTML = html;
        });
    }

    // Remove row button (delegation)
    if (subjectRows) {
        subjectRows.addEventListener('click', function(e) {
            if (e.target.classList.contains('remove-row') || e.target.closest('.remove-row')) {
                const btn = e.target.closest('.remove-row');
                const row = btn.closest('tr');
                if (row) row.remove();
            }
        });
    }

    // ------------------------------------------
    // AUTO CALCULATION: Total, Percentage, Grade
    // ------------------------------------------
    if (calculateBtn) {
        calculateBtn.addEventListener('click', function() {
            const obtainedInputs = document.querySelectorAll('.obtained');
            const totalInputs = document.querySelectorAll('.total');
            
            let totalObtained = 0;
            let totalMarks = 0;
            
            for (let i = 0; i < obtainedInputs.length; i++) {
                const obt = parseFloat(obtainedInputs[i].value) || 0;
                const tot = parseFloat(totalInputs[i].value) || 0;
                totalObtained += obt;
                totalMarks += tot;
            }
            
            document.getElementById('totalObtained').value = totalObtained;
            document.getElementById('totalMarks').value = totalMarks;
            
            let percentage = 0;
            if (totalMarks > 0) {
                percentage = (totalObtained / totalMarks) * 100;
            }
            document.getElementById('percentage').value = percentage.toFixed(2);
            
            // Grade calculation (same logic as backend)
            let grade = 'N/A';
            if (percentage >= 90) grade = 'A+';
            else if (percentage >= 80) grade = 'A';
            else if (percentage >= 70) grade = 'B';
            else if (percentage >= 60) grade = 'C';
            else if (percentage >= 50) grade = 'D';
            else if (percentage > 0) grade = 'F';
            document.getElementById('grade').value = grade;
        });
    }

    // ------------------------------------------
    // SEARCH & SORT: already handled by server.
    // Additional client-side confirmation for delete (already in HTML)
    // ------------------------------------------

    // ------------------------------------------
    // BOOTSTRAP ALERTS AUTO-DISMISS (optional)
    // ------------------------------------------
    setTimeout(function() {
        let alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            let bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
});