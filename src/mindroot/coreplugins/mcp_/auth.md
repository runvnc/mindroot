Base Protocol
Authorization

Copy page

Protocol Revision: 2025-03-26
​
Introduction
​
Purpose and Scope
The Model Context Protocol provides authorization capabilities at the transport level, enabling MCP clients to make requests to restricted MCP servers on behalf of resource owners. This specification defines the authorization flow for HTTP-based transports.
​
Protocol Requirements
Authorization is OPTIONAL for MCP implementations. When supported:
Implementations using an HTTP-based transport SHOULD conform to this specification.
Implementations using an STDIO transport SHOULD NOT follow this specification, and instead retrieve credentials from the environment.
Implementations using alternative transports MUST follow established security best practices for their protocol.
​
Standards Compliance
This authorization mechanism is based on established specifications listed below, but implements a selected subset of their features to ensure security and interoperability while maintaining simplicity:
OAuth 2.1 IETF DRAFT
OAuth 2.0 Authorization Server Metadata (RFC8414)
OAuth 2.0 Dynamic Client Registration Protocol (RFC7591)
​
Authorization Flow
​
Overview
MCP auth implementations MUST implement OAuth 2.1 with appropriate security measures for both confidential and public clients.
MCP auth implementations SHOULD support the OAuth 2.0 Dynamic Client Registration Protocol (RFC7591).
MCP servers SHOULD and MCP clients MUST implement OAuth 2.0 Authorization Server Metadata (RFC8414). Servers that do not support Authorization Server Metadata MUST follow the default URI schema.
​
OAuth Grant Types
OAuth specifies different flows or grant types, which are different ways of obtaining an access token. Each of these targets different use cases and scenarios.
MCP servers SHOULD support the OAuth grant types that best align with the intended audience. For instance:
Authorization Code: useful when the client is acting on behalf of a (human) end user.
For instance, an agent calls an MCP tool implemented by a SaaS system.
Client Credentials: the client is another application (not a human)
For instance, an agent calls a secure MCP tool to check inventory at a specific store. No need to impersonate the end user.
​
Example: authorization code grant
This demonstrates the OAuth 2.1 flow for the authorization code grant type, used for user auth.
NOTE: The following example assumes the MCP server is also functioning as the authorization server. However, the authorization server may be deployed as its own distinct service.
A human user completes the OAuth flow through a web browser, obtaining an access token that identifies them personally and allows the client to act on their behalf.
When authorization is required and not yet proven by the client, servers MUST respond with HTTP 401 Unauthorized.
Clients initiate the OAuth 2.1 IETF DRAFT authorization flow after receiving the HTTP 401 Unauthorized.
The following demonstrates the basic OAuth 2.1 for public clients using PKCE.
MCP Server
Client
User-Agent (Browser)
MCP Server
Client
User-Agent (Browser)
Generate code_verifier and code_challenge
User logs in and authorizes
Begin standard MCP message exchange
MCP Request
HTTP 401 Unauthorized
Open browser with authorization URL + code_challenge
GET /authorize
Redirect to callback URL with auth code
Callback with authorization code
Token Request with code + code_verifier
Access Token (+ Refresh Token)
MCP Request with Access Token
​
Server Metadata Discovery
For server capability discovery:
MCP clients MUST follow the OAuth 2.0 Authorization Server Metadata protocol defined in RFC8414.
MCP server SHOULD follow the OAuth 2.0 Authorization Server Metadata protocol.
MCP servers that do not support the OAuth 2.0 Authorization Server Metadata protocol, MUST support fallback URLs.
The discovery flow is illustrated below:
Server
Client
Server
Client
Use endpoints from metadata
Fall back to default endpoints
alt
[Discovery Success]
[Discovery Failed]
Continue with authorization flow
GET /.well-known/oauth-authorization-server
200 OK + Metadata Document
404 Not Found
​
Server Metadata Discovery Headers
MCP clients SHOULD include the header MCP-Protocol-Version: <protocol-version> during Server Metadata Discovery to allow the MCP server to respond based on the MCP protocol version.
For example: MCP-Protocol-Version: 2024-11-05
​
Authorization Base URL
The authorization base URL MUST be determined from the MCP server URL by discarding any existing path component. For example:
If the MCP server URL is https://api.example.com/v1/mcp, then:
The authorization base URL is https://api.example.com
The metadata endpoint MUST be at https://api.example.com/.well-known/oauth-authorization-server
This ensures authorization endpoints are consistently located at the root level of the domain hosting the MCP server, regardless of any path components in the MCP server URL.
​
Fallbacks for Servers without Metadata Discovery
For servers that do not implement OAuth 2.0 Authorization Server Metadata, clients MUST use the following default endpoint paths relative to the authorization base URL:
Endpoint	Default Path	Description
Authorization Endpoint	/authorize	Used for authorization requests
Token Endpoint	/token	Used for token exchange & refresh
Registration Endpoint	/register	Used for dynamic client registration
For example, with an MCP server hosted at https://api.example.com/v1/mcp, the default endpoints would be:
https://api.example.com/authorize
https://api.example.com/token
https://api.example.com/register
Clients MUST first attempt to discover endpoints via the metadata document before falling back to default paths. When using default paths, all other protocol requirements remain unchanged.
​
Dynamic Client Registration
MCP clients and servers SHOULD support the OAuth 2.0 Dynamic Client Registration Protocol to allow MCP clients to obtain OAuth client IDs without user interaction. This provides a standardized way for clients to automatically register with new servers, which is crucial for MCP because:
Clients cannot know all possible servers in advance
Manual registration would create friction for users
It enables seamless connection to new servers
Servers can implement their own registration policies
Any MCP servers that do not support Dynamic Client Registration need to provide alternative ways to obtain a client ID (and, if applicable, client secret). For one of these servers, MCP clients will have to either:
Hardcode a client ID (and, if applicable, client secret) specifically for that MCP server, or
Present a UI to users that allows them to enter these details, after registering an OAuth client themselves (e.g., through a configuration interface hosted by the server).
​
Authorization Flow Steps
The complete Authorization flow proceeds as follows:
MCP Server
Client
User-Agent (Browser)
MCP Server
Client
User-Agent (Browser)
alt
[Server Supports Discovery]
[No Discovery]
alt
[Dynamic Client Registration]
Generate PKCE Parameters
User /authorizes
GET /.well-known/oauth-authorization-server
Authorization Server Metadata
404 (Use default endpoints)
POST /register
Client Credentials
Open browser with authorization URL + code_challenge
Authorization Request
Redirect to callback with authorization code
Authorization code callback
Token Request + code_verifier
Access Token (+ Refresh Token)
API Requests with Access Token
​
Decision Flow Overview
Available

Not Available

Available

Not Available

Start Auth Flow

Check Metadata Discovery

Use Metadata Endpoints

Use Default Endpoints

Check Registration Endpoint

Perform Dynamic Registration

Alternative Registration Required

Start OAuth Flow

Generate PKCE Parameters

Request Authorization

User Authorization

Exchange Code for Tokens

Use Access Token

​
Access Token Usage
​
Token Requirements
Access token handling MUST conform to OAuth 2.1 Section 5 requirements for resource requests. Specifically:
MCP client MUST use the Authorization request header field Section 5.1.1:

Copy
Authorization: Bearer <access-token>
Note that authorization MUST be included in every HTTP request from client to server, even if they are part of the same logical session.
Access tokens MUST NOT be included in the URI query string
Example request:

Copy
GET /v1/contexts HTTP/1.1
Host: mcp.example.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
​
Token Handling
Resource servers MUST validate access tokens as described in Section 5.2. If validation fails, servers MUST respond according to Section 5.3 error handling requirements. Invalid or expired tokens MUST receive a HTTP 401 response.
​
Security Considerations
The following security requirements MUST be implemented:
Clients MUST securely store tokens following OAuth 2.0 best practices
Servers SHOULD enforce token expiration and rotation
All authorization endpoints MUST be served over HTTPS
Servers MUST validate redirect URIs to prevent open redirect vulnerabilities
Redirect URIs MUST be either localhost URLs or HTTPS URLs
​
Error Handling
Servers MUST return appropriate HTTP status codes for authorization errors:
Status Code	Description	Usage
401	Unauthorized	Authorization required or token invalid
403	Forbidden	Invalid scopes or insufficient permissions
400	Bad Request	Malformed authorization request
​
Implementation Requirements
Implementations MUST follow OAuth 2.1 security best practices
PKCE is REQUIRED for all clients
Token rotation SHOULD be implemented for enhanced security
Token lifetimes SHOULD be limited based on security requirements
​
Third-Party Authorization Flow
​
Overview
MCP servers MAY support delegated authorization through third-party authorization servers. In this flow, the MCP server acts as both an OAuth client (to the third-party auth server) and an OAuth authorization server (to the MCP client).
​
Flow Description
The third-party authorization flow comprises these steps:
MCP client initiates standard OAuth flow with MCP server
MCP server redirects user to third-party authorization server
User authorizes with third-party server
Third-party server redirects back to MCP server with authorization code
MCP server exchanges code for third-party access token
MCP server generates its own access token bound to the third-party session
MCP server completes original OAuth flow with MCP client
Third-Party Auth Server
MCP Server
MCP Client
User-Agent (Browser)
Third-Party Auth Server
MCP Server
MCP Client
User-Agent (Browser)
User authorizes
Generate bound MCP token
Initial OAuth Request
Redirect to Third-Party /authorize
Authorization Request
Redirect to MCP Server callback
Authorization code
Exchange code for token
Third-party access token
Redirect to MCP Client callback
MCP authorization code
Exchange code for token
MCP access token
​
Session Binding Requirements
MCP servers implementing third-party authorization MUST:
Maintain secure mapping between third-party tokens and issued MCP tokens
Validate third-party token status before honoring MCP tokens
Implement appropriate token lifecycle management
Handle third-party token expiration and renewal
​
Security Considerations
When implementing third-party authorization, servers MUST:
Validate all redirect URIs
Securely store third-party credentials
Implement appropriate session timeout handling
Consider security implications of token chaining
Implement proper error handling for third-party auth failures
​
Best Practices
​
Local clients as Public OAuth 2.1 Clients
We strongly recommend that local clients implement OAuth 2.1 as a public client:
Utilizing code challenges (PKCE) for authorization requests to prevent interception attacks
Implementing secure token storage appropriate for the local system
Following token refresh best practices to maintain sessions
Properly handling token expiration and renewal
​
Authorization Metadata Discovery
We strongly recommend that all clients implement metadata discovery. This reduces the need for users to provide endpoints manually or clients to fallback to the defined defaults.
​
Dynamic Client Registration
Since clients do not know the set of MCP servers in advance, we strongly recommend the implementation of dynamic client registration. This allows applications to automatically register with the MCP server, and removes the need for users to obtain client ids manually.
