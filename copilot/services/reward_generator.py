import random
import string

class RewardGenerator:
    
    def __init__(self):
        self.categories = {
            "shopping": ["Amazon", "Walmart", "Instacart", "Target"],
            "utilities": ["PayPal"],
            "transport": ["Uber", "Lyft", "Amtrak", "Delta"],
            "dining": ["Starbucks", "McDonald’s", "Subway", "Taco Bell", "UberEats", "Doordash", "GrubHub", "Domino's", "Chipotle"],
            "health": ["CVS", "Walgreens", "Rite Aid", "ISO Health", "Geico"],
        }

    def generate_coupon(self, category_name):
        if category_name not in self.categories:
            return "Invalid category"

        brand = random.choice(self.categories[category_name])
        amount = round(random.randint(5, 25)/5)*5
        coupon_code = 'HACKNC25'+''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

        # return f"You have received coupon of ${amount} of {brand} of code: {coupon_code}"
        return f"Congratulations! Enjoy a ${amount} coupon at {brand}! Use code: {coupon_code} 🎉"