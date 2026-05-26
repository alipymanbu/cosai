<template>
    <div class="sidebar">
        <div class="user">
            <div class="avatar-frame">
                <img src="../../public/田园犬.png" alt="user">
            </div>
            <p>用户</p>
        </div>
        <div class="search">
            <input type="text" id="search-input" name="search" placeholder="Ctrl+F 搜索">
        </div>
        <div class="menu">
            <ul>
                <li>
                    <a href="#">
                        <img src="../../public/胶囊.png" alt="图标1">
                        <span>图标</span>
                    </a>
                </li>
            </ul>
        </div>
    </div>
   
</template>

<script lang="ts">

    export default {
        name: 'Sidebar',
        setup() {
            
        }
    }
</script>

<style scoped lang="scss">
.sidebar {
    display: flex;
    flex-direction: column;
  
    width: 200px;
    height: 100vh;
    background-color: #f5f5f5;
    padding: 20px;
    border-left: 1px solid #ccc;
    border-right: 1px solid #ccc;
    .user {
        display: flex;
        // justify-content: space-evenly;
        .avatar-frame {
            border: 1px solid #ccc;
            background-color: #fff;
            border-radius: 10%;
            margin-right: 10px;
            img {
                width: 45px;
                
            }
        }
    }
    .search {
        margin-top: 10px;
        input {
            font-size: 15px;
            width: 100%;
            height: 35px;
            padding: 10px;
            border: 1px solid #ccc;
            border-radius: 5px;
            outline: none;
        }
        input:hover {
            border-color: #ffffff;
        }
    }
    .menu {
        margin-top: 20px;
        ul {
            border-top: 1px solid #ccc;
            li:nth-child(1) {
                margin-top: 10px;
                
                a {
                    display: flex;
                    align-items: center;
                    img {
                        margin-left: 10px;
                        width: 30px;
                        margin-right: 10px;
                    }
                }
            }
            li:nth-child(1):hover {
               
                border-radius: 10px;
                background-color: #e0e0e0;
            }
        }
    }
}


</style>