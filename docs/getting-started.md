
After installing the Jub Client library, you can start using it in your project by importing the necessary modules and initializing the client. Here's a simple example to get you started:

```python
from jub_client import JubClient
# Initialize the Jub Client
client = JubClient(host='your_host_here', port=your_port_here, api_key='your_api_key_here')
# Example: Fetching data from the API
response = client.get_data(endpoint='your_endpoint_here')
print(response)
```

⚠️ `<api_key>` is under development and may not be available in the current version. Please check the documentation for updates on authentication methods.

