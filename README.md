# Exploring how researchers utilize generative AI applications for research productivity

This code was used in the master's thesis on the usefulness of argument feedback in research. For the user studies in this work, the application was hosted at [https://paperfeedback.streamlit.app/](https://paperfeedback.streamlit.app/). To run the application on your own machine, follow these steps:

1. `git clone https://github.com/lunavandenbergh/paperhelp`
2. `pip install -r requirements.txt`
3. `streamlit run app.py`

To make the local instance of the application functional, you will need to add API keys locally. To do this, add a file to the `.streamlit` folder named `secrets.toml` and add your API keys. You will need one for gemini, and for sonar. The file will look something like this:
```
PERPLEXITY_API_KEY="insert-your-key-here"
GEMINI_API_KEY="insert-your-key-here"
```
Now, the application is fully functional on your machine.
