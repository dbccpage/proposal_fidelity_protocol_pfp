# Renders demo/demo.gif. Run from code/rust/pfp_cli after `cargo build --release`:
#   vhs demo/demo.tape
Output demo/demo.gif

Set Shell "bash"
Set FontSize 15
Set Width 1120
Set Height 520
Set Padding 24
Set TypingSpeed 35ms
Set Theme "Builtin Dark"

Hide
Type "export PATH=$PWD/target/release:$PATH PS1='$ ' && clear"
Enter
Show

Type "pfp check --prompt demo/prompt.md demo/reply.json"
Sleep 400ms
Enter
Sleep 5s

Type "pfp explain self_certification"
Sleep 400ms
Enter
Sleep 5s
