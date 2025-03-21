console.log("sanity check!");

fetch("/config/")
.then((result) => { return result.json(); })
.then((data) => {
      // Initialize Stripe.js
  const stripe = Stripe(data.publicKey);
  console.log(stripe);
});


