import {defineConfig} from "@hey-api/openapi-ts";
import {defaultPlugins} from "@hey-api/openapi-ts";

export default defineConfig({
  client: "@hey-api/client-fetch",
  input: "../backend/openapi.json",
  output: {
    path: "src/api/wallstr-sdk",
    format: "prettier",
    lint: "eslint",
  },
  plugins: [
    ...defaultPlugins,
    {
      name: "@hey-api/sdk",
      asClass: true,
      operationId: true,
    },
  ],
});
