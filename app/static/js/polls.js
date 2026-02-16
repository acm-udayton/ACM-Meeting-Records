let questionIndex = 0;

function addQuestion() {
  const questionsContainer = document.getElementById("questions-container");

  const questionDiv = document.createElement("div");
  questionDiv.className = "card p-3 mb-4";
  
  const currentQuestionIndex = questionIndex;

  questionDiv.innerHTML = `
    <div class="mb-3">
      <label>Question ${questionIndex + 1}</label>
      <i class="fa fa-trash delete-question-btn" title="Delete Question" style="cursor: pointer; float: right; color: red;"></i>
      <input
        type="text"
        name="questions-${currentQuestionIndex}-question_text"
        class="form-control"
        placeholder="Enter question"
        required
      >
    </div>

    <div class="form-check mb-2 form-check form-switch">
      <input 
        type="checkbox" 
        class="form-check-input frq-checkbox " 
        id="frq-checkbox-${currentQuestionIndex}"
        name="questions-${currentQuestionIndex}-is_free_response"
      >
      <label class="form-check-label" for="frq-checkbox-${currentQuestionIndex}">
        Make this a free response question
      </label>
    </div>

    <div class="form-check mb-3 multi-response-section form-check form-switch">
      <input 
        type="checkbox" 
        class="form-check-input multi-response-checkbox" 
        id="multi-response-checkbox-${currentQuestionIndex}"
        name="questions-${currentQuestionIndex}-allow_multiple_responses"
      >
      <label class="form-check-label" for="multi-response-checkbox-${currentQuestionIndex}">
        Allow multiple responses (users can select multiple options)
      </label>
    </div>

    <div class="options-section">
      <div class="options-container"></div>
      <button type="button" class="btn btn-sm add-option-btn mb-2 add-option-btn">
        + Add Option
      </button>
    </div>
  `;

  const optionsContainer = questionDiv.querySelector(".options-container");
  const addOptionBtn = questionDiv.querySelector(".add-option-btn");
  const frqCheckbox = questionDiv.querySelector(".frq-checkbox");
  const multiResponseCheckbox = questionDiv.querySelector(".multi-response-checkbox");
  const optionsSection = questionDiv.querySelector(".options-section");
  const multiResponseSection = questionDiv.querySelector(".multi-response-section");

  let optionIndex = 0;

  function addOption() {
    const optionDiv = document.createElement("div");
    optionDiv.className = "input-group mb-2 option-input";
    optionDiv.innerHTML = `
      <input
        type="text"
        class="form-control"
        placeholder="Option ${optionIndex + 1}"
        name="questions-${currentQuestionIndex}-options-${optionIndex}-option_text"
        required
      >
      <button type="button" class="btn btn-sm remove-option-btn">×</button>
    `;

    const removeBtn = optionDiv.querySelector(".remove-option-btn");
    removeBtn.onclick = () => {
      optionDiv.remove();
    };

    optionsContainer.appendChild(optionDiv);
    optionIndex++;
  }

  // Toggle options visibility and requirements based on FRQ checkbox
  frqCheckbox.onchange = () => {
    if (frqCheckbox.checked) {
      // Hide options section and multi-response option
      optionsSection.style.display = "none";
      multiResponseSection.style.display = "none";
      multiResponseCheckbox.checked = false;
      
      // Remove all option inputs when switching to FRQ
      optionsContainer.innerHTML = "";
      optionIndex = 0;
    } else {
      // Show options section and multi-response option
      optionsSection.style.display = "block";
      multiResponseSection.style.display = "block";
      
      // Add two default options if none exist
      if (optionsContainer.children.length === 0) {
        addOption();
        addOption();
      }
    }
  };

  addOptionBtn.onclick = addOption;

  // Add two default options initially
  addOption();
  addOption();

  questionsContainer.appendChild(questionDiv);
  questionIndex++;
}

function deleteQuestion(event) {
  if (event.target.classList.contains("delete-question-btn")) {
    const questionCard = event.target.closest(".card");
    questionCard.remove();
  }
}

document.getElementById("questions-container").addEventListener("click", deleteQuestion);  

// Add one question by default on page load
addQuestion();