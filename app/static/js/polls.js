let questionIndex = 0;

function addQuestion() {
  const questionsContainer = document.getElementById("questions-container");

  const questionDiv = document.createElement("div");
  questionDiv.className = "card p-3 mb-4";
  
  const currentQuestionIndex = questionIndex; // Capture current index

  questionDiv.innerHTML = `
    <div class="mb-3">
      <label>Question ${questionIndex + 1}</label>
      <input
        type="text"
        name="questions[${currentQuestionIndex}][text]"
        class="form-control"
        placeholder="Enter question"
        required
      >
    </div>

    <div class="options-container"></div>

    <button type="button" class="btn btn-sm btn-outline-primary mb-2">
      + Add Option
    </button>
  `;

  const optionsContainer = questionDiv.querySelector(".options-container");
  const addOptionBtn = questionDiv.querySelector("button");

  let optionIndex = 0;

  function addOption() {
    const optionInput = document.createElement("input");
    optionInput.type = "text";
    optionInput.className = "form-control mb-2";
    optionInput.placeholder = `Option ${optionIndex + 1}`;
    optionInput.name = `questions[${currentQuestionIndex}][options][${optionIndex}]`;
    optionInput.required = true;

    optionsContainer.appendChild(optionInput);
    optionIndex++;
  }

  addOptionBtn.onclick = addOption;

  // Add two default options
  addOption();
  addOption();

  questionsContainer.appendChild(questionDiv);
  questionIndex++;
}

// Add one question by default on page load
addQuestion();