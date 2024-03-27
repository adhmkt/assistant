document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('userForm');
    const submitButton = document.querySelector('.form-chat-submit');
    const successMessage = document.createElement('div');
  
    form.onsubmit = function(e) {
      e.preventDefault(); // Prevent the default form submission behavior
      user_access_tool(); // Call the function to process the form data
  
      // Disable the submit button and show the success message
      submitButton.disabled = true;
      successMessage.textContent = 'Pedido Enviado Com Sucesso. Entraremos em contato!';
      form.appendChild(successMessage);
    };
  });
  
  function user_access_tool() {
    // Function to process the form submission.
    // This is where you'll handle the form data without leaving the page.
    console.log('Processing form data...');
    // Add your code here to process the form data
  }
  