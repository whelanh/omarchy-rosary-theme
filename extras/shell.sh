# Rosary shell colours (sourced by the living-themes ~/.bashrc snippet).
# eza: parchment dirs, olive executables, gold sizes, oxblood write bits.
export EZA_COLORS="di=1;38;2;233;223;204:ex=1;38;2;143;162;134:ln=38;2;201;162;193:or=38;2;194;91;98:\
sn=38;2;217;180;91:sb=38;2;139;106;74:da=38;2;132;125;110:uu=38;2;184;174;155:gu=38;2;111;143;201:\
ur=38;2;217;180;91:uw=38;2;194;91;98:ux=38;2;143;162;134:ue=38;2;143;162;134:\
gr=38;2;111;143;201:gw=38;2;178;110;100:gx=38;2;110;140;120:tr=38;2;111;143;201:tw=38;2;178;110;100:tx=38;2;110;140;120:\
xx=38;2;38;44;64:ga=38;2;143;162;134:gm=38;2;217;180;91:gd=38;2;194;91;98:gn=38;2;201;162;193"

# fzf: transparent night, gold matches, a rosary bead as the pointer.
export FZF_DEFAULT_OPTS="\
--color=bg:-1,bg+:#2a3048,fg:#b8ae9b,fg+:#f2eadb,hl:#d9b45b,hl+:#efd28c \
--color=border:#3a3a4e,label:#d9b45b,prompt:#d9b45b,pointer:#efd28c,marker:#8fa286 \
--color=spinner:#c9a2c1,info:#847d6e,header:#c9a2c1,query:#f2eadb,gutter:-1,scrollbar:#3a3a4e \
--layout=reverse --border=rounded --border-label=' ✝ rosary ' --border-label-pos=3 \
--prompt='✝ ' --pointer='•' --marker='+' --info=inline-right --height=45%"
