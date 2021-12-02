<!-- Title: testing locked files -->
<!-- Space: MARK -->
# Github Action: Publish to Confluence

This action publishes markdown files from a Github repository to Confluence.

The action pushes all `.md` files to Confluence. It maintains the folder hierarchy and uses `README.md` or `index.md` files as roots for each folder.

## Inputs

- `confluence_url` - URL to your Confluence instance
- `confluence_username` - username to use for accessing Confluence APIs
- `confluence_token` - token to use for accessing Confluence APIs
- `confluence_space` - space key on Confluence to publish to

## Example workflow configuration

```yml
on: [push]

jobs:
  confluence_job:
    runs-on: ubuntu-latest
    name: Upload to Confluence
    steps:
      - uses: actions/checkout@v2
      - name: Publish
        uses: snowplow-incubator/action-publish-to-confluence@v1
        with:
          confluence_url: https://xyz.atlassian.net/wiki
          confluence_space: XYZ
          confluence_username: ${{ secrets.CONFLUENCE_USERNAME }}
          confluence_token: ${{ secrets.CONFLUENCE_TOKEN }}
```
