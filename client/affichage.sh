cd /usr/local/share/pycafe-client
pc=$(cat /sys/class/net/eth0/address | tr -d :)
sed -i "s/=dede@station3/=$USER@PC$pc/g" "$HOME/.mission-control/accounts/accounts.cfg"
sed -i "s/=dede/=$USER/g" "$HOME/.mission-control/accounts/accounts.cfg"
sed -i "s/=Dede/=$USER/g" "$HOME/.mission-control/accounts/accounts.cfg"
sed -i "s/=Accueil/=$USER/g" "$HOME/.mission-control/accounts/accounts.cfg"
python ./affichage.py > ~/.pycafe-gui.log
/usr/bin/gnome-session-quit --logout --force --no-prompt
