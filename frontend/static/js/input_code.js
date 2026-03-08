document.addEventListener('DOMContentLoaded', function() {
    const inputs = document.querySelectorAll('.code-input');
    const correctCode = '123456';
    
    inputs.forEach((input, index) => {
        input.addEventListener('input', function() {
            this.value = this.value.replace(/[^0-9]/g, '');
            if (this.value && index < inputs.length - 1) {
                inputs[index + 1].focus();
            }
            checkCode();
        });
        
        input.addEventListener('keydown', function(e) {
            if (e.key === 'Backspace' && !this.value && index > 0) {
                inputs[index - 1].focus();
            }
        });
    });
    
    function checkCode() {
        let code = '';
        inputs.forEach(input => code += input.value);
        
        if (code.length === inputs.length) {
            if (code === correctCode) {
                alert('Код верный!');
                document.getElementById('codeForm').submit();
            } else {
                alert('Неверный код!');
                inputs.forEach(input => input.value = '');
                inputs[0].focus();
            }
        }
    }
    
    inputs[0].focus();
});
