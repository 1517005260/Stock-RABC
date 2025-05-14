import SvgIcon from '@/components/Svglcon'

const svgRequired = require.context('./svg', false, /\.svg$/)
svgRequired.keys().forEach((item) => svgRequired(item))

export default (app) => {
    app.component('svg-icon', SvgIcon)
}