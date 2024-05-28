# This script enables streaming chat from Ollama using streamlit.
# If the user interrupts with a 'stop' or '/...' prompt, the stream will be interrupted but not lost. 
#
# EXAMPLE USAGE:
# $ (activate a virtual environment)
# $ pip3 install -r requirements.pip
# export MODEL='qwen:0.5b' # or whatever other model you want
# streamlit run shutup_llama.py 

import ollama
import streamlit as st 
from os import environ
from typing import Dict, Generator

# String contstants for select models
QWEN_500M = 'qwen:0.5b'

# String constants for session state
KEY_INTERRUPT_MSG = 'interrupt_msg'
KEY_MESSAGES = 'messages'

st.title('Try interrupting with "/" or "stop".')

# SESSION_STATE INITIALIZATION
# session_state is basically a dict of things that streamlit manages in-memory
if not KEY_MESSAGES in st.session_state:
    st.session_state[KEY_MESSAGES] = [] 
# initialize the model from environment variables 
st.session_state.selected_model = environ.get('MODEL', QWEN_500M)
# Keep track of some state which can be used to capture interrupted reply streams
if not KEY_INTERRUPT_MSG in st.session_state:
    # if not is necessary so you don't clear the 'interrupt_msg' field on every prompt
    st.session_state[KEY_INTERRUPT_MSG] = ''



def ollama_generator(model_name: str, messages: Dict) -> Generator:
    stream = ollama.chat(
        model=model_name, messages=messages, stream=True)
    for chunk in stream:
        st.session_state[KEY_INTERRUPT_MSG] += chunk['message']['content']
        yield chunk['message']['content']

# Display chat messages from history on app rerun 
for msg in st.session_state[KEY_MESSAGES]:
    with st.chat_message(msg['role']):
        st.markdown(msg['content'])

def interrupt(prompt: str) -> bool:
    # indicate if a prompt should interrupt further streaming
    if prompt.strip().startswith('/') or prompt.strip().lower() in ('stop', 'bye'):
        return True 
    return False 

# ... for each input from the user...
if prompt := st.chat_input('What is up?'):
    if not interrupt(prompt):
        # DURING NORMAL EXECUTION, FIRST SHOW THE INPUT FROM THE USER....
        st.session_state[KEY_MESSAGES].append({'role':'user', 'content':prompt})
        with st.chat_message('user'): # 'user' arg means style the message as coming from the user
            st.markdown(prompt)
        # ... THEN STREAM THE REPLY....
        with st.chat_message("assistant"):
            response = st.write_stream(ollama_generator(
                st.session_state.selected_model, st.session_state.messages))
            st.session_state.messages.append(
                {"role": "assistant", "content": response})
    else:
        # BUT IF THE REPLY WAS INTERRUPTED, YOU NEED TO CAPTURE IT FIRST....
        with st.chat_message('assistant'):
            st.session_state[KEY_MESSAGES].append({'role':'assistant', 'content':st.session_state[KEY_INTERRUPT_MSG]+'...'})
            st.markdown(st.session_state[KEY_INTERRUPT_MSG]+'...')
            st.session_state[KEY_INTERRUPT_MSG] = '' # reset for the next interruption
        # ... THE POST THE USERS PROMPT- NOTHING MORE WILL HAPPEN UNTIL THE NEXT PROMPT
        st.session_state[KEY_MESSAGES].append({'role':'user', 'content':prompt})
        with st.chat_message('user'): # 'user' arg means style the message as coming from the user
            st.markdown(prompt)
    
if __name__ == '__main__':
    quit("Don't run me as main! Try streamlit run ...")

