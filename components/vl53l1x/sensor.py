import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import i2c, sensor
from esphome.const import (
    CONF_ID,
    CONF_DISTANCE,
    CONF_UPDATE_INTERVAL,
    DEVICE_CLASS_DISTANCE,
    STATE_CLASS_MEASUREMENT,
    UNIT_MILLIMETER,
)

CODEOWNERS = ["@mrtoy-me"]
DEPENDENCIES = ["i2c"]

vl53l1x_ns = cg.esphome_ns.namespace("vl53l1x")

VL53L1XComponent = vl53l1x_ns.class_(
    "VL53L1XComponent", cg.PollingComponent, i2c.I2CDevice
)

DistanceMode = vl53l1x_ns.enum("DistanceMode")

DISTANCE_MODES = {
    "short": DistanceMode.SHORT,
    "long": DistanceMode.LONG, 
}

CONF_DISTANCE_MODE = "distance_mode"
CONF_RANGE_STATUS = "range_status"
CONF_ROI = "roi"

ROI_WIDTH_MIN = 4
ROI_WIDTH_MAX = 16
ROI_HEIGHT_MIN = 4
ROI_HEIGHT_MAX = 16

def validate_update_interval(config):
    if config[CONF_UPDATE_INTERVAL].total_milliseconds < 1000:
        raise cv.Invalid(
            f"VL53L1X update_interval must be 1 second or greater. Increase update_interval to >= 1 second"
        )
    return config

def validate_roi(value) -> list[int]:
    try:
        width, height = cv.dimensions(value)
    except cv.Invalid as e:
        raise cv.Invalid(f"ROI {e.msg}") from e

    if not (ROI_WIDTH_MIN <= width <= ROI_WIDTH_MAX):
        raise cv.Invalid(f"ROI width must be between {ROI_WIDTH_MIN} and {ROI_WIDTH_MAX}")

    if not (ROI_HEIGHT_MIN <= height <= ROI_HEIGHT_MAX):
        raise cv.Invalid(f"ROI height must be between {ROI_HEIGHT_MIN} and {ROI_HEIGHT_MAX}")

    return [width, height]

CONFIG_SCHEMA = cv.All(
    cv.Schema(   
        {
            cv.GenerateID(): cv.declare_id(VL53L1XComponent),
            cv.Optional(CONF_DISTANCE_MODE, default="long"): cv.enum(
                DISTANCE_MODES, upper=False
            ),
            cv.Optional(CONF_DISTANCE): sensor.sensor_schema(
                unit_of_measurement=UNIT_MILLIMETER,
                accuracy_decimals=0,
                device_class=DEVICE_CLASS_DISTANCE,
                state_class=STATE_CLASS_MEASUREMENT,
            ),
            cv.Optional(CONF_ROI): validate_roi,
            cv.Optional(CONF_RANGE_STATUS): sensor.sensor_schema(
                accuracy_decimals=0,
                state_class=STATE_CLASS_MEASUREMENT,
            ),
        }
    )
    .extend(cv.polling_component_schema("60s"))
    .extend(i2c.i2c_device_schema(0x29)),
    validate_update_interval,
)

async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)
    await i2c.register_i2c_device(var, config)

    if CONF_DISTANCE in config:
      sens = await sensor.new_sensor(config[CONF_DISTANCE])    
      cg.add(var.set_distance_sensor(sens))

    if CONF_RANGE_STATUS in config:
        sens = await sensor.new_sensor(config[CONF_RANGE_STATUS])    
        cg.add(var.set_range_status_sensor(sens))

    cg.add(var.config_distance_mode(config[CONF_DISTANCE_MODE]))
    if CONF_ROI in config:
        width, height = config[CONF_ROI]
        cg.add(var.config_roi(width, height))
