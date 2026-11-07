# Zbalermorna on Discord

It might be desirable to use these fonts on Discord to communicate with other people that have these fonts. This is possible with [BeautifulDiscord, a css injector](https://github.com/leovoel/BeautifulDiscord). Once you have it installed and are editing your css file, you can use something like this to make the input area, messages, and code blocks render using Zbalermorna-compatible fonts:

```
@import url(//jackhumbert.github.io/zbalermorna/assets/css/fonts.css);

body {
    font-family: Whitney, "Helvetica Neue", Helvetica, Arial, sans-serif, 'crisa';
}
code {
    font-family: Consolas, "Liberation Mono", Menlo, Courier, monospace, "fira-code-zlm";
}
::placeholder, body, button, input, select, textarea {
    font-family: Whitney, "Helvetica Neue", Helvetica, Arial, sans-serif, 'crisa';
}
```

These use the default Discord fonts, and define a Zbalermorna-compatible font as the back-up, so the general look of Discord doesn't change.
