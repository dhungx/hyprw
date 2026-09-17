# ~/.zshrc

# ── Lịch sử lệnh ──────────────────────────────
HISTFILE=~/.zsh_history
HISTSIZE=10000
SAVEHIST=10000
setopt HIST_IGNORE_DUPS       # không lưu lệnh gõ trùng liên tiếp
setopt HIST_IGNORE_SPACE      # lệnh bắt đầu bằng dấu cách thì không lưu
setopt SHARE_HISTORY          # nhiều tab/terminal dùng chung 1 lịch sử
setopt APPEND_HISTORY

# ── Tuỳ chọn zsh ──────────────────────────────
setopt AUTO_CD                # gõ tên thư mục là tự cd, khỏi gõ "cd" trước
setopt EXTENDED_GLOB
unsetopt BEEP

# ── Completion (gợi ý khi bấm Tab) ────────────
autoload -Uz compinit
compinit
zstyle ':completion:*' menu select
zstyle ':completion:*' matcher-list 'm:{a-zA-Z}={A-Za-z}'

# ── Phím tắt — giống bash/app thường, tránh bỡ ngỡ khi chuyển từ Windows ──
bindkey '^[[1;5C' forward-word       # Ctrl+→ nhảy theo từ
bindkey '^[[1;5D' backward-word      # Ctrl+←
bindkey '^[[H' beginning-of-line     # Home
bindkey '^[[F' end-of-line           # End
bindkey '^[[3~' delete-char          # Delete

# ── Alias tiện dụng ────────────────────────────
alias ls='ls --color=auto'
alias ll='ls -lah'
alias la='ls -A'
alias grep='grep --color=auto'
alias update='sudo pacman -Syu'
alias cleanup='sudo pacman -Rns $(pacman -Qtdq)'   # xoá package mồ côi không ai cần
alias hyprreload='hyprctl reload'
alias htop='btop'    # dùng btop thay htop, đã theme sẵn Catppuccin Mocha
alias top='btop'

# ── Plugin: autosuggestions ────────────────────
# Gợi ý lệnh mờ dựa theo lịch sử — bấm → (phím mũi tên phải) để nhận gợi ý
# Cần cài: zsh-autosuggestions
if [ -f /usr/share/zsh/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh ]; then
    source /usr/share/zsh/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh
    ZSH_AUTOSUGGEST_HIGHLIGHT_STYLE="fg=#6c7086"   # màu xám Catppuccin, khớp theme
fi

# ── Plugin: syntax highlighting ────────────────
# Lệnh đúng/sai đổi màu ngay khi gõ (xanh = lệnh tồn tại, đỏ = không có)
# Cần cài: zsh-syntax-highlighting
# LƯU Ý: PHẢI source ở cuối file — quy tắc bắt buộc của chính plugin này,
# source sớm hơn sẽ làm autosuggestions phía trên không chạy đúng.
if [ -f /usr/share/zsh/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh ]; then
    source /usr/share/zsh/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
fi

# ── Prompt ──────────────────────────────────────
# Cần cài: starship. Nếu chưa cài, dòng dưới không lỗi gì, chỉ dùng prompt
# mặc định của zsh.
if command -v starship >/dev/null 2>&1; then
    eval "$(starship init zsh)"
fi
