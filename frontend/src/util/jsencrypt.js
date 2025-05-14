import JSEncrypt from 'jsencrypt/bin/jsencrypt.min'

// 密钥对生成 http://web.chacuo.net/netrsakeypair

const publicKey =
    'MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAluxDXjjVGkHPTNpEdnVc\n' +
    'q+0Tch44bAbzLD6cW8KmW4Kkxe6LbS1NRB0m6npLKJ1ZOqJztlucylha8V0l9yiV\n' +
    'AxAfQq/gmXsrehoaj4Kj5tPDF4vByUplFASecomxxd8LEbnDEfE4cC23PrfVtye1\n' +
    'SfwiEYY3HCTfnLhQAJr+fnRFPvf4Uv9w+typ6IqMDwCy6ybewNTuOK0hMy2uecRg\n' +
    'd2xSQVrRzoCczVuTD1MrS1QChV5vewDAeTeI45D+zyXKzLM/dC2ZmqEpBTCAbDHi\n' +
    'h3CcF3m+K69su2TMmRP0pW3px2I4FA4hy/MlPm2nmtf12XF9NzeViZHGyETeFFzh\n' +
    'cQIDAQAB'

const privateKey =
    'MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCW7ENeONUaQc9M\n' +
    '2kR2dVyr7RNyHjhsBvMsPpxbwqZbgqTF7ottLU1EHSbqeksonVk6onO2W5zKWFrx\n' +
    'XSX3KJUDEB9Cr+CZeyt6GhqPgqPm08MXi8HJSmUUBJ5yibHF3wsRucMR8ThwLbc+\n' +
    't9W3J7VJ/CIRhjccJN+cuFAAmv5+dEU+9/hS/3D63KnoiowPALLrJt7A1O44rSEz\n' +
    'La55xGB3bFJBWtHOgJzNW5MPUytLVAKFXm97AMB5N4jjkP7PJcrMsz90LZmaoSkF\n' +
    'MIBsMeKHcJwXeb4rr2y7ZMyZE/SlbenHYjgUDiHL8yU+baea1/XZcX03N5WJkcbI\n' +
    'RN4UXOFxAgMBAAECggEAE+8AtuEqxF0M1Em/4SV/J/YYK2pyaVJBrAZZAIWlE1Ee\n' +
    'EkZ/g9wH6IcxLKcaZjLiJixuvBc9jjw9RsPWz948UDtA5b31HFB4XZg1Cd9nZoVx\n' +
    'rxp2be+1if9SLi6hnFDpVV4Dtcr2eVqQaWg+ggJsn2j91vKzNLRqFHkDmBDgrDLb\n' +
    'RXD9w+YbysX+2DJQC5Li1cQHL/n1nEOqFA0qX8uA8VkbbsPRzYLoBXQAjRdf45q3\n' +
    '/II4EeYFm1s8kTyAy4+XFN7njFp5S2H3yhKC/7L+e7pLlm15sYTQfs6L65KL3jRS\n' +
    'MtbbynsEa6IOnzjv/d9Qv3BlY4bBht1UwHlK3sjiQQKBgQDGfuxtQxxuzfZGQwtR\n' +
    'tExmVSplJeaKn+kVibQijQKHF+hYdZ5mBz0XpYIKAHxLLgew0Sl7Ord9A/6xUhqH\n' +
    'SFR0wpyq8YMCRbhtttjFftThgWMwv5JQRow3ONYBgmgVyjCSRLxmYh8pEPHaEPZG\n' +
    'LBYNyzbj1fNRa/Om1k90asJTywKBgQDCpS7wLoewwmCpu7P7e0Sr6nxUGqkjDsp7\n' +
    'lOm9s1OSfI57OB7UUNM1aUTGEXGzTySzcS8j7B0IvZiqt/8pNeO2cJhXm6+hGHrb\n' +
    'IJxuNCps81aMciKTTrRr0hVWYfSF334oc7Xyx3/NeQn7K1mXpiRfVpgmRuGxBYSz\n' +
    'pdTmWQyQMwKBgEKNCY30o1LPQVP7ZI8nSTpCMa2qEGrIBKkQ+1FeP8u1i1QlU09X\n' +
    '+/ayqi/aS9IVA8UXy7WiUSTcMweWxIg5Cv/+w/JYeRlI8PXwCSvmQ0+8RtpwUIkT\n' +
    'ri1RpAbrhyRPHwvbeeNF4LavFLeNWlTasSY8zRGEiUjyTcXRMuCQbskTAoGBAKHV\n' +
    'Jw6JEUZUhnv41S79EV6CijZ/KCs+y/kuGZ0gsRZ1Ox2VzoQmY0TgLk8kB83WuqP7\n' +
    'Mf+C+6zdvkYKzzqbVKXGPdNxXPfq25K/LXCvLKsDMu14o+ioIngW5qi4rs5zwHev\n' +
    'pRKi7k6PGU5cf5QHjew6miwQ+OrutKOM+FNArKJjAoGAeN+yTleYx2Of8wKsQ9gz\n' +
    '9VNU8yHim3bRYH8LUMsScuLIU9cbx4O1OeStSR9cmo/4VB0PPziCmNBd+y+wxebp\n' +
    'UTAqVHTp3L/L6AmsG4zT0wo4xw6H+MsAY4AZDzRXu5zD/Sh+SwLl0ClVexEeHefu\n' +
    'iLIvRhp/hSHRJTlCqF1W2ws='

// 加密
export function encrypt(txt) {
    const encryptor = new JSEncrypt()
    encryptor.setPublicKey(publicKey) // 设置公钥
    return encryptor.encrypt(txt) // 对数据进行加密
}

// 解密
export function decrypt(txt) {
    const encryptor = new JSEncrypt()
    encryptor.setPrivateKey(privateKey) // 设置私钥
    return encryptor.decrypt(txt) // 对数据进行解密
}