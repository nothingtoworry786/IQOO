// app.config.js — extends app.json with dynamic environment injection.
//
// Set APP_ENV=staging or APP_ENV=production in your CI / EAS build profile
// to switch the API base URL. Defaults to 'development' in dev builds.
//
// Physical Android device testing: in config/env.ts, change the development
// apiBaseUrl to your machine's LAN IP (e.g. http://192.168.1.50:8000)
// because 'localhost' on an Android device resolves to the device itself.

export default ({ config }) => ({
  ...config,
  extra: {
    ...config.extra,
    environment: process.env.APP_ENV || "development",
  },
});
