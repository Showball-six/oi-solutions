# [P5658 [CSP-S 2019] 括号树](https://www.luogu.com.cn/problem/P5658)

**思路**：

对于括号匹配，通常有两种判断方式：

- 使用栈：遇到左括号入栈，遇到右括号时，如果栈为空，说明不合法。否则弹出栈顶。最终判断栈是否为空。
- 使用前缀和：将左括号标记为 $1$，右括号标记为 $-1$。维护前缀和，如果中途出现了负数或最终前缀和不等于零则不合法。

很容易想到**从根节点到 $u$ 的合法括号子串的数量=从根节点到 $fa[u]$ 的合法括号子串的数量+以 $u$ 结尾新产生的合法括号子串**。

令 $f_u$ 表示以 $u$ 结尾新产生的合法括号子串数量。

如果 $s_u=$'$($' ，$f_u=0$。如果 $s_u=$ '$)$' 且栈为空，则 $f_u=0$。栈不为空，令栈顶为 $k$ 节点。则 $f_u=f_{fa[k]}+1$ 。

因为以 $u$ 结尾新产生的合法括号子串数量分为 $s[k,u]$ 接在以 $k$ 的父亲节点为结尾的合法子串之后的所有情况，以及 $s[k,u]$ 自己成为一段。

**参考代码**：

```CPP
#include<bits/stdc++.h>

using namespace std;

using i64=long long;

const int N=5e5+10;

vector<i64> e[N];
stack<i64> stk;
i64 n,fa[N],f[N],cnt[N];
string s;

void dfs(i64 u){
    cnt[u]=cnt[fa[u]];
    if(s[u]=='('){
        stk.push(u);
        for(auto v:e[u]) dfs(v);
        stk.pop();
    }else if(stk.empty()){
        for(auto v:e[u]) dfs(v);
    }else{
        int k=stk.top();
        f[u]=f[fa[k]]+1;
        cnt[u]+=f[u];
        stk.pop();
        for(auto v:e[u]) dfs(v);
        stk.push(k);
    }
}

void Showball(){
    cin>>n>>s;
    s="?"+s;
    for(int i=2;i<=n;i++){
        cin>>fa[i];
        e[fa[i]].push_back(i);
    }

    dfs(1);

    i64 ans=0;
    for(i64 i=1;i<=n;i++) ans^=i*cnt[i];
    cout<<ans<<"\n";
}
int main(){
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int t=1;
    //cin>>t;

    while(t--){
      Showball();
    }

    return 0;
}
```
