# 💼 Finance Copilot – Expense tracking made effortless - just WhatsApp it!

![WhatsApp](https://img.shields.io/badge/WhatsApp-25D366?style=for-the-badge&logo=whatsapp&logoColor=white)
![Django](https://img.shields.io/badge/django-%23092E20.svg?style=for-the-badge&logo=django&logoColor=white)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![MongoDB](https://img.shields.io/badge/MongoDB-%234ea94b.svg?style=for-the-badge&logo=mongodb&logoColor=white)
![Google Gemini](https://img.shields.io/badge/google%20gemini-8E75B2?style=for-the-badge&logo=google%20gemini&logoColor=white)
![Twilio](https://img.shields.io/badge/Twilio-F22F46?style=for-the-badge&logo=Twilio&logoColor=white)

## Inspiration  
Manually tracking expenses is tedious, and traditional budgeting apps require constant input, making them inconvenient. We wanted to create a seamless solution that integrates effortlessly into daily life. Inspired by the ubiquity of WhatsApp, we're thrilled to present **Finance Copilot**—a chatbot that lets users track expenses via text, images, or voice notes without opening another app. This is our official submission for Hack_NCState 2025!

## What We Learned  
Throughout this project, we gained hands-on experience with:  
- **Large Language Models (LLMs)**, specifically **Google Gemini**, for extracting financial data from user inputs.  
- **WhatsApp chatbot integration** using **Twilio API** to facilitate smooth and responsive interactions.  
- **Django for server-side management**, ensuring efficient request handling and transaction processing.  
- **MongoDB Atlas** as a NoSQL database for scalable and efficient storage of financial data.  

## How We Built It  
1. **Tech Stack**  
   - **Backend:** Django (Python) for handling chatbot interactions and transaction processing.  
   - **AI Processing:** Google Gemini API for understanding and categorizing transactions from text, images, and voice inputs.  
   - **Database:** MongoDB Atlas for storing user transactions and budgeting data.  
   - **Messaging Platform:** Twilio API for WhatsApp chatbot integration.  

2. **Key Features**  
   - Users can **log expenses via text, voice, or image**.  
   - We **categorize transactions** with the help of Google Gemini and provide spending insights.  
   - A **reward system** incentivizes users to stay within budget.  

## Challenges We Faced  
- **Processing multimodal inputs:** Handling text, images, and voice required optimizing prompt engineering for Google Gemini.  
- **Ensuring accurate categorization:** Fine-tuning LLM prompts to improve transaction classification.  
- **Seamless WhatsApp integration:** Designing a conversational flow that extracts structured data while maintaining a natural user experience.  
- **Optimizing database queries:** Structuring MongoDB documents efficiently for fast retrieval and analytics.  
- **Building a meaningful reward system:** Creating an incentive mechanism that genuinely encourages better spending habits.  

## Conclusion  
**Finance Copilot** transforms expense tracking by making it **intuitive, automated, and rewarding**. By leveraging **LLMs, WhatsApp, and a robust backend**, we eliminate manual entry and provide valuable financial insights. 
