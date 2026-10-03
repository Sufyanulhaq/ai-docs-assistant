# Security and single sign on

## Single sign on

Single sign on uses SAML 2.0 and works with Okta, Microsoft Entra ID and Google Workspace. It is available on the Business plan only. SCIM provisioning, which creates and removes users automatically from your identity provider, is also part of Business.

To set it up, an Owner opens Settings, then Security, then Single sign on, and follows the steps to exchange metadata with the identity provider. Test with one account before you require SSO for everyone.

## Two factor authentication

Two factor authentication with an authenticator app or a hardware security key is available on every plan. On Pro and Business an Owner can require it for all members of the workspace.

## Audit logs

Audit logs record sign ins, role changes, API key creation and deletion, and billing changes. They are kept for 1 year and are available on the Business plan.

## Data protection

- Data is encrypted in transit with TLS 1.2 or newer.
- Data is encrypted at rest with AES 256.
- You choose the data region, United States or European Union, when you create the workspace. The region cannot be changed afterwards, so create a new workspace if you need to move.

## Compliance reports

A SOC 2 Type II report is available on request under an NDA. Email security@fernhill.example.

## Reporting a vulnerability

Please report security problems to security@fernhill.example. Do not post them in public channels. We reply within 2 business days.
