document.querySelectorAll(".btn.btn-confirm").forEach(button => {
    button.addEventListener("click", async function () {
        const amount = this.dataset.amount;
        const currency = this.dataset.currency;
        const description = this.dataset.description;

        try {
            // Call OutSystems API to create PaymentIntent
            const response = await fetch("https://personal-xnaxqorr.outsystemscloud.com/PaymentAPI/rest/PaymentAPI/PostPaymentIntents", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    amount: parseInt(amount), // Amount in cents
                    currency: currency,
                    description: description,
                    // confirm: "False" // Do not confirm yet
                }),
            });

            if (!response.ok) {
                const errorText = await response.text();
                console.error(`API returned status ${response.status}. Response: ${errorText}`);
                const result = JSON.parse(errorText);
                if (result && result.Errors) {
                    alert(`An error occurred: ${result.Errors[0]}`);
                } else {
                    alert(`An error occurred: ${errorText}`);
                }
                throw new Error(`API returned status ${response.status}. Response: ${errorText}`);
            }

            const result = await response.json();
            console.log("API Response:", result);
            console.log("API client:", result.client_secret);

            // Redirect user to Stripe's hosted payment page
            if (result && result.client_secret) {
                const stripe = Stripe('pk_test_51QAsReGgLeDXJUjvDrRwiHI6nisUuA7gSQw3AlX2UBqzlc4vPhbGCQCjcNiDel8pBfks9UhZGZXlO0jkvuNx1roP00zHKPl3aR'); // Replace with your publishable key

                // Redirect user for payment
                stripe.redirectToCheckout({
                    sessionId: result.client_secret,
                }).then(function (result) {
                    if (result.error) {
                        console.error("Stripe Checkout Error:", result.error.message);
                        alert(`An error occurred: ${result.error.message}`);
                    }
                });
            } else {
                throw new Error("Client secret not returned from API.");
            }
        } catch (error) {
            console.error("Error:", error);
            alert(`An error occurred while processing payment: ${error.message}`);
        }
    });
});
