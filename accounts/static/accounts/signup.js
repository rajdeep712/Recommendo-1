const continueBtn = document.querySelector(".continue-button");
const continueText = continueBtn.querySelector(".continue-text");
const Lottie = document.getElementById("loginLottie");

const form = continueBtn.closest("form");

form.addEventListener("submit", function(e) {
    if (!continueBtn.disabled) {
        continueBtn.disabled = true;
        continueBtn.style.cursor = "not-allowed";
        continueText.style.display = "none";
        Lottie.style.display = "block";
    }
});